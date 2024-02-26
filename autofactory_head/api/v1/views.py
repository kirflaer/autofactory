import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, generics
from rest_framework.exceptions import APIException
from rest_framework.response import Response

import api.views
from api.v1.routers import get_task_router, get_content_router
from api.v1.services import get_marks_to_unload, task_take_pallet_collect, task_take
from tasks.models import TaskStatus
from tasks.serializers import TaskPropertiesSerializer
from tasks.task_services import (change_task_properties, get_task_queryset, TaskException, get_content_queryset,
                                 RouterTask)
from warehouse_management.models import (
    Pallet,
    PalletStatus,
    StorageCell,
    ShipmentOperation,
    SelectionOperation,
    TypeCollect,
)
from warehouse_management.serializers import (PalletReadSerializer, PalletWriteSerializer, PalletUpdateSerializer,
                                              StorageCellsSerializer)
from warehouse_management.warehouse_services import create_pallets


class TasksViewSet(viewsets.ViewSet):
    router = dict[str: RouterTask]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = self.get_routers()

    def get_routers(self) -> dict[str: RouterTask]:
        return get_task_router()

    def list(self, request, type_task):
        task_router = self.router.get(type_task.upper())
        if not task_router:
            raise APIException('Тип задачи не найден')

        filter_task = {key: value for key, value in request.query_params.items()}
        filter_task['user'] = self.request.user

        if task_router.task in (ShipmentOperation, SelectionOperation):
            filter_value = {
                'SHIPMENT': TypeCollect.SHIPMENT,
                'SELECTION': TypeCollect.SELECTION,
                'SHIPMENT_MOVEMENT': TypeCollect.MOVEMENT,
                'SELECTION_MOVEMENT': TypeCollect.MOVEMENT,
            }
            filter_task['subtype_task'] = filter_value.get(type_task.upper())

        try:
            task_queryset = get_task_queryset(task_router.task, filter_task)
        except TaskException:
            raise APIException('Не найден переданный фильтр')

        serializer = task_router.read_serializer(data=task_queryset, many=True)
        serializer.request_user = request.user
        serializer.is_valid()
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, type_task):
        task_router = self.router.get(type_task.upper())
        if not task_router:
            raise APIException('Тип задачи не найден')

        if isinstance(request.data, list):
            serializer = task_router.write_serializer(data=request.data, many=True)
        else:
            serializer = task_router.write_serializer(data=request.data)

        if serializer.is_valid():
            response = {'type_task': type_task}
            result = task_router.create_function(serializer.validated_data, request.user)
            answer_serializer = task_router.answer_serializer
            if not answer_serializer:
                response = response | {'guids': result}
            else:
                serializer = answer_serializer(result, many=True)
                response = response | {'pallets': serializer.data}
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def take(self, request, type_task, guid):
        task_router = self.router.get(type_task.upper())
        if not task_router:
            raise APIException('Тип задачи не найден')
        instance = task_router.task.objects.filter(guid=guid).first()
        if instance is None:
            raise APIException('Задача не найдена')
        if instance.status == TaskStatus.WORK:
            raise APIException('Задача уже в работе')

        if type_task == 'PALLET_COLLECT_SHIPMENT':
            task_take_pallet_collect(instance, request.user, guid)

        task_take(instance, request.user)

        return Response({'type_task': type_task, 'guid': guid, 'status': TaskStatus.WORK})


class TasksChangeViewSet(TasksViewSet):
    def change_task(self, request, type_task, guid):
        task_router = self.router.get(type_task.upper())
        if not task_router:
            raise APIException('Тип задачи не найден')

        instance = task_router.task.objects.filter(guid=guid).first()
        if instance is None:
            raise APIException('Задача не найдена')

        serializer = TaskPropertiesSerializer(data=request.data)
        if serializer.is_valid():
            change_task_properties(instance, serializer.validated_data)
            return Response({'status': serializer.validated_data})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TasksContentViewSet(viewsets.ViewSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO здесь будут прочие роутеры
        self.router = get_content_router()

    def list(self, request, type_task, content_type):
        content_router = self.router.get(content_type.upper())
        if not content_router:
            raise APIException('Не найден тип контента')

        filter_task = {key: value for key, value in request.query_params.items()}

        try:
            content_queryset = get_content_queryset(content_router, type_task, filter_task)
        except TaskException:
            raise APIException('Не найден переданный фильтр')

        serializer = content_router.serializer(content_queryset, many=True)
        return Response(serializer.data)


class MarksViewSet(api.views.MarksViewSet):
    @staticmethod
    def marks_to_unload(request):
        """ Формирует марки для выгрузки в 1с """
        return Response(data=get_marks_to_unload())


class PalletViewSet(viewsets.ViewSet):
    @staticmethod
    def create(request):
        serializer = PalletWriteSerializer(data=request.data, many=True)

        if serializer.is_valid():
            create_pallets(serializer.validated_data)
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def list(request):
        queryset = Pallet.objects.all()

        if len(request.query_params):
            if request.query_params.get('id') is not None:
                queryset = queryset.filter(id=request.query_params.get('id'))

        serializer = PalletReadSerializer(queryset, many=True)
        return Response(serializer.data)


class PalletRetrieveUpdate(generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = Pallet.objects.all().exclude(status=PalletStatus.ARCHIVED)
    lookup_field = 'id'
    adv_lookup_field = 'guid'
    serializer_class = PalletReadSerializer

    def get_serializer_class(self):
        if self.request.stream is None:
            return PalletReadSerializer
        else:
            return PalletUpdateSerializer

    def get_object(self):

        include_archive_pallets = self.request.query_params.get('include_archive_pallets', 'false')
        if include_archive_pallets == 'true':
            self.queryset = Pallet.objects.all().order_by('content_count')

        filter_value = self.kwargs[self.lookup_field]
        try:
            uuid.UUID(filter_value)
        except ValueError:
            return super().get_object()

        filter_kwargs = {self.adv_lookup_field: self.kwargs[self.lookup_field]}
        return get_object_or_404(self.queryset, **filter_kwargs)


class StorageCellsListCreateViewSet(generics.ListCreateAPIView):
    """Список и создание складских ячеек"""
    queryset = StorageCell.objects.all()
    serializer_class = StorageCellsSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.META['REQUEST_METHOD'] == 'GET':
            return super().get_serializer(*args, **kwargs)
        else:
            return StorageCellsSerializer(data=self.request.data, many=True)
