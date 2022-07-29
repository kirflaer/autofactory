from rest_framework import status, permissions, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

import api.views
from api.v1.services import get_marks_to_unload
from tasks.serializers import TaskPropertiesSerializer
from tasks.task_services import change_task_properties


class TasksChangeViewSet(api.views.TasksViewSet):
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


class MarksViewSet(api.views.MarksViewSet):
    @staticmethod
    def marks_to_unload(request):
        """ Формирует марки для выгрузки в 1с """
        return Response(data=get_marks_to_unload())

