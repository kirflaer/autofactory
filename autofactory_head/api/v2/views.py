from json import JSONDecodeError

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters
from rest_framework.exceptions import APIException
from rest_framework.response import Response

import api.views
from api.v2.services import get_marks_to_unload
from tasks.models import TaskStatus
from tasks.task_services import change_task_properties
from warehouse_management.models import Pallet
from warehouse_management.serializers import PalletReadSerializer, PalletWriteSerializer
from warehouse_management.warehouse_services import create_pallets


class TasksChangeViewSet(api.views.TasksViewSet):
    def change_task(self, request, type_task, guid):
        task_router = self.router.get(type_task.upper())
        if not task_router:
            raise APIException('Тип задачи не найден')

        instance = task_router.task.objects.filter(guid=guid).first()
        if instance is None:
            raise APIException('Задача не найдена')

        try:
            task_data = task_router.content_model(**request.data)
        except TypeError:
            raise APIException('Переданы некорректные данные')
        except JSONDecodeError:
            raise APIException('Переданы некорректные данные')

        if task_data.properties is not None:
            change_task_properties(instance, task_data.__dict__['properties'])

        instance = task_router.task.objects.get(guid=guid)
        if instance.status == TaskStatus.CLOSE and not instance.closed:
            instance.close()

        if task_data.content is not None:
            ret = task_router.change_content_function(task_data.__dict__['content'].__dict__, instance)
            return Response(ret)

        return Response({'status': 'success'})


class MarksViewSet(api.views.MarksViewSet):
    @staticmethod
    def marks_to_unload(request):
        """ Формирует марки для выгрузки в 1с """
        return Response(data=get_marks_to_unload())


class PalletViewSet(generics.ListCreateAPIView):
    serializer_class = PalletReadSerializer
    queryset = Pallet.objects.all().order_by('-content_count')
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('id', 'batch_number', 'production_date', 'content_count')
    search_fields = ('id',)

    def create(self, request, *args, **kwargs):
        serializer = PalletWriteSerializer(data=request.data, many=True)
        if serializer.is_valid():
            create_pallets(serializer.validated_data)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
