import base64
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from catalogs.models import (ActivationKey, Department, Device, Direction, Line, LineProduct, Organization, Product,
                             RegularExpression, Storage, TypeFactoryOperation, Unit, StorageCell)
from factory_core.models import Shift
from packing.marking_services import create_marking_marks, remove_marks
from packing.models import MarkingOperation, RawMark
from tasks.models import TaskStatus
from tasks.task_services import get_task_queryset, TaskException, get_content_queryset
from warehouse_management.models import Pallet, PalletStatus
from warehouse_management.serializers import PalletReadSerializer, PalletUpdateSerializer

from api.exceptions import ActivationFailed
from warehouse_management.warehouse_routers import get_task_router, get_content_router
from .serializers import (ConfirmUnloadingSerializer, DepartmentSerializer,
                          DeviceSerializer, DirectionSerializer, LineCreateSerializer, LogSerializer,
                          MarksSerializer, OrganizationSerializer, ProductSerializer,
                          RegularExpressionSerializer, StorageSerializer, TypeFactoryOperationSerializer,
                          UnitSerializer, UserSerializer, LineSerializer, StorageCellsSerializer, MarkingSerializer,
                          AggregationsSerializer)
from .services import confirm_marks_unloading

User = get_user_model()


class OrganizationList(generics.ListAPIView):
    """Список организаций"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class UserRetrieve(generics.RetrieveAPIView):
    """Данные пользователя"""
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        instance = request.user
        serializer = UserSerializer(instance)
        return Response(serializer.data)


class TypeFactoryOperationViewSet(generics.ListCreateAPIView):
    """ Типы производственных операций"""
    queryset = TypeFactoryOperation.objects.all()
    serializer_class = TypeFactoryOperationSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return TypeFactoryOperationSerializer(data=self.request.data,
                                                  many=True)


class ProductViewSet(generics.ListCreateAPIView):
    """Список и создание товаров"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.META['REQUEST_METHOD'] == 'GET':
            return super().get_serializer(*args, **kwargs)
        else:
            return ProductSerializer(data=self.request.data, many=True)


class StorageList(generics.ListAPIView):
    """Список складов"""
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer


class DepartmentList(generics.ListCreateAPIView):
    """Список и создание подразделений"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return DepartmentSerializer(data=self.request.data, many=True)


class DirectionListCreateView(generics.ListCreateAPIView):
    """Список и создание подразделений"""
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return DirectionSerializer(data=self.request.data, many=True)


class LineListCreateView(generics.ListCreateAPIView):
    """Список линий"""
    queryset = Line.objects.all()
    serializer_class = LineSerializer

    def perform_create(self, serializer):
        for element in serializer.validated_data:
            values = {'name': element.get('name')}

            managers = {'storage': Storage.objects,
                        'department': Department.objects,
                        'type_factory_operation': TypeFactoryOperation.objects}

            for key, value in managers.items():
                serializer_data = element.get(key)
                values[key] = value.filter(
                    external_key=serializer_data).first()

            line = Line.objects.create(**values)

            for key in element.get('products'):
                product = Product.objects.filter(external_key=key).first()
                if not LineProduct.objects.filter(product=product, line=line).exists():
                    LineProduct.objects.create(product=product, line=line)

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return LineCreateSerializer(data=self.request.data, many=True)


class DeviceViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def list_scanners(request):
        """Список автоматических сканеров"""
        queryset = Device.objects.all()
        queryset = queryset.filter(mode=Device.AUTO_SCANNER)
        serializer = DeviceSerializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    def create(request):
        """Создает устройство пользователя и связывает с пользователем
        Если устройство найдено по идентификатору то просто связывает"""
        if request.user.device is not None:
            raise APIException("У пользователя уже определено устройство")

        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data.get('identifier')
            number = None
            if not serializer.validated_data.get('activation_key') is None:
                number = serializer.validated_data.pop('activation_key')

            if Device.objects.filter(identifier=identifier).exists():
                instance = Device.objects.get(identifier=identifier)
            else:
                instance = serializer.save(mode=Device.DCT)

            if number is not None:
                activation_key = ActivationKey.objects.filter(number=number).first()
                if activation_key is None:
                    activation_key = ActivationKey.objects.create(number=number)

                if activation_key.device.count() and activation_key.device.first() != instance:
                    raise ActivationFailed('Код активирован на другом устройстве')
                instance.activation_key = activation_key
                instance.save()

            request.user.device = instance
            request.user.save()

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def remove(request):
        """Очищает связанное устройство у пользователя"""
        if request.user.device is None:
            raise APIException('У пользователя не определено устройство')

        request.user.device = None
        request.user.save()
        return Response({'detail': 'success'})


class MarkingListCreateViewSet(generics.ListCreateAPIView):
    """Используется для создания маркировок и отображения списка маркировок"""

    queryset = MarkingOperation.objects.all()[:100]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('line', 'closed', 'unloaded', 'guid')

    def get_queryset(self):
        """ Добавляем нестандартные фильтры """
        queryset = self.queryset
        storage = self.request.query_params.get('storage')
        if storage is not None:
            queryset = queryset.filter(line__storage=storage)
        return queryset

    def marking_close(self, instance: MarkingOperation, validated_data: dict):
        pass

    def get_model_not_required_fields(self):
        return {'product': Product, 'organization': Organization}

    def get_marking_init_data(self, serializer: MarkingSerializer) -> dict:
        line = serializer.validated_data.get('line')
        line = self.request.user.line if line is None else line

        values = {'author': self.request.user,
                  'line': line}

        model_not_required_fields = self.get_model_not_required_fields()

        for key, value in model_not_required_fields.items():
            guid = serializer.validated_data.get(key)
            if guid is None:
                continue
            values[key] = value.objects.filter(pk=guid).first()
        return values


class MarksViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def confirm_unloading(request):
        """ Подтверждение об успешной выгрузке маркировки """
        serializer = ConfirmUnloadingSerializer(data=request.data)
        if serializer.is_valid():
            confirm_marks_unloading(serializer.validated_data['operations'])
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def add_marks(request):
        """Добавляет марки в существующую операцию маркировки"""
        serializer = MarksSerializer(data=request.data, source='post_request')
        if serializer.is_valid():
            operation = MarkingOperation.objects.get(
                guid=serializer.validated_data['marking'])
            create_marking_marks(operation,
                                 [{'mark': i} for i in
                                  serializer.validated_data['marks']])
            return Response({'detail': 'success'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def remove_marks(request):
        """ Удаляет марки из текущей маркировки """
        serializer = MarksSerializer(data=request.data)
        if serializer.is_valid():
            remove_marks(serializer.validated_data['marks'])
            return Response(serializer.data)
        return Response(serializer.errors)


class LogCreateViewSet(generics.CreateAPIView):
    serializer_class = LogSerializer

    def perform_create(self, serializer):
        data = serializer.validated_data.pop('data')
        serializer.save(server_version=settings.VERSION,
                        username=self.request.user.username,
                        device=self.request.user.device,
                        level=self.request.user.log_level,
                        data=base64.b64decode(data))


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

        filter_value = self.kwargs[self.lookup_field]
        try:
            uuid.UUID(filter_value)
        except ValueError:
            return super().get_object()

        filter_kwargs = {self.adv_lookup_field: self.kwargs[self.lookup_field]}
        return get_object_or_404(self.queryset, **filter_kwargs)


class TasksViewSet(viewsets.ViewSet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = get_task_router()

    def list(self, request, type_task):
        task_router = self.router.get(type_task.upper())
        if not task_router:
            raise APIException('Тип задачи не найден')

        filter_task = {key: value for key, value in request.query_params.items()}
        filter_task['user'] = self.request.user

        try:
            task_queryset = get_task_queryset(task_router.task, filter_task)
        except TaskException:
            raise APIException('Не найден переданный фильтр')

        serializer = task_router.read_serializer(data=task_queryset, many=True)
        serializer.request_user = request.user
        serializer.is_valid()
        serializer.save()
        return Response(serializer.data)

    def create(self, request, type_task):
        task_router = self.router.get(type_task.upper())
        if not task_router:
            raise APIException('Тип задачи не найден')

        serializer = task_router.write_serializer(data=request.data, many=True)
        if serializer.is_valid():
            # TODO: обработать ошибку создания
            result = task_router.create_function(serializer.validated_data, request.user)
            return Response({'type_task': type_task, 'guids': result})
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

        instance.status = TaskStatus.WORK
        instance.user = request.user
        instance.save()

        return Response({'type_task': type_task, 'guid': guid, 'status': TaskStatus.WORK})


class RegExpList(generics.ListAPIView):
    """Список организаций"""
    queryset = RegularExpression.objects.all()
    serializer_class = RegularExpressionSerializer


class UnitsCreateListSet(generics.ListCreateAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

    def get_serializer(self, *args, **kwargs):
        return UnitSerializer(data=self.request.data, many=True)


class StorageCellsListCreateViewSet(generics.ListCreateAPIView):
    """Список и создание складских ячеек"""
    queryset = StorageCell.objects.all()
    serializer_class = StorageCellsSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.META['REQUEST_METHOD'] == 'GET':
            return super().get_serializer(*args, **kwargs)
        else:
            return StorageCellsSerializer(data=self.request.data, many=True)


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


class MarkingViewSet(viewsets.ViewSet):
    def close_marking(self, instance: MarkingOperation, validated_data: dict):
        pass

    def close(self, request, pk=None):
        """Закрывает текущую маркировку
        Если закрытие происходит с ТСД отправляется набор марок
        Если закрытие от автоматического сканера марки берутся из RawMark"""

        marking = MarkingOperation.objects.filter(guid=pk)

        if not marking.exists():
            raise APIException("Маркировка не найдена")

        marking = MarkingOperation.objects.get(guid=pk)
        if marking.closed:
            raise APIException("Маркировка уже закрыта")

        if request.user.role == User.PACKER:
            serializer = AggregationsSerializer(data=request.data, many=True)
            if serializer.is_valid():
                data = serializer.data
            else:
                return Response(serializer.errors)
        elif request.user.role == User.VISION_OPERATOR:
            data = RawMark.objects.filter(operation=marking).values()
        else:
            data = []

        self.close_marking(marking, data)
        return Response({'detail': 'success'})
