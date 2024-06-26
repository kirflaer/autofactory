from json import JSONDecodeError

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from pydantic.error_wrappers import ValidationError
from rest_framework import generics, status, filters
from rest_framework.exceptions import APIException
from rest_framework.response import Response

import api.views
from api.v1.views import TasksViewSet
from api.v2.serializers import MarkingSerializer
from api.v2.services import get_marks_to_unload
from catalogs.models import ExternalSource
from packing.marking_services import marking_close
from packing.models import MarkingOperation
from tasks.models import TaskStatus, Task
from tasks.task_services import change_task_properties, RouterTask
from warehouse_management.models import Pallet, PalletStatus
from warehouse_management.serializers import PalletReadSerializer, PalletWriteSerializer
from warehouse_management.warehouse_services import create_pallets, get_pallet_filter_from_shipment, \
    get_pallets_in_acceptance

User = get_user_model()


class MarksViewSet(api.views.MarksViewSet):
    @staticmethod
    def marks_to_unload(request):
        """ Формирует марки для выгрузки в 1с """
        return Response(data=get_marks_to_unload())


class PalletViewSet(generics.ListCreateAPIView):
    serializer_class = PalletReadSerializer
    queryset = Pallet.objects.all().exclude(status=PalletStatus.ARCHIVED).order_by('content_count')
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('id', 'batch_number', 'production_date', 'content_count', 'product', 'status', 'series')
    search_fields = ('id',)

    def create(self, request, *args, **kwargs):
        serializer = PalletWriteSerializer(data=request.data, many=True)
        if serializer.is_valid():
            pallets = create_pallets(serializer.validated_data)
            headers = self.get_success_headers(serializer.validated_data)
            serializer = PalletReadSerializer(pallets, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        # реализация фильтров на вхождение в диапазон
        list_params = {
            'ids': 'id__in',
            'guids': 'guid__in',
            'keys': 'external_key__in',
            'external_task_key': get_pallet_filter_from_shipment,
            'pallets_in_acceptance': get_pallets_in_acceptance
        }

        qs = super().get_queryset()
        for param, condition in list_params.items():
            value = self.request.query_params.get(param)
            if not value:
                continue
            if callable(condition):
                qs_filter = condition(value)
            else:
                qs_filter = {condition: value.split('_')}

            qs = qs.filter(**qs_filter)

        return qs


class MarkingListCreateViewSet(api.views.MarkingListCreateViewSet):
    serializer_class = MarkingSerializer

    def perform_create(self, serializer):
        values = self.get_marking_init_data(serializer)
        if serializer.validated_data.get('aggregations') is None:
            serializer.save(**values)
        else:
            # оффлайн маркировка
            data = serializer.validated_data.pop('aggregations')
            instance = serializer.save(**values)
            marking_close(instance, data)


class MarkingViewSet(api.views.MarkingViewSet):
    def close_marking(self, instance: MarkingOperation, validated_data: dict):
        marking_close(instance, validated_data)


class TasksChangeViewSet(TasksViewSet):

    def change_task(self, request, type_task, guid):
        task_router = self.router.get(type_task.upper())
        if not task_router:
            raise APIException('Тип задачи не найден')

        instance = task_router.task.objects.filter(guid=guid).first()
        if instance is None:
            external_source = ExternalSource.objects.filter(external_key=guid).first()
            instance = task_router.task.objects.filter(external_source=external_source).first()

        if instance is None:
            raise APIException('Задача не найдена')

        guid = instance.pk

        try:
            task_data = task_router.content_model(**request.data)
        except TypeError:
            raise APIException('Переданы некорректные данные, возможно указана некорректная базовая модель')
        except JSONDecodeError:
            raise APIException('Переданы некорректные данные, возможно не указана некорректная базовая модель')
        except ValidationError:
            raise APIException(
                'Переданы некорректные данные, возможно не верно указаны значения передаваемых полей')

        old_status = instance.status
        if task_data.properties is not None:
            change_task_properties(instance, task_data.__dict__['properties'])
            if task_router.change_properties_function is not None:
                instance = task_router.task.objects.get(guid=guid)
                content = task_data.__dict__['properties'].__dict__
                content['user'] = request.user
                task_router.change_properties_function(content, instance)

        instance = task_router.task.objects.get(guid=guid)

        if old_status != instance.status and instance.user is None:
            instance.user = request.user
            instance.save()

        if instance.status == TaskStatus.CLOSE and not instance.closed:
            instance.close()

        result = {'status': 'success'}
        if task_data.content is not None:
            result = task_router.change_content_function(task_data.__dict__['content'].__dict__, instance)

        return Response(result)
