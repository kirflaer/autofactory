from json import JSONDecodeError

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

import api.views
from tasks.models import TaskStatus
from tasks.task_services import change_task_properties


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

        if instance.status == TaskStatus.CLOSE and not instance.closed:
            instance.close()

        if task_data.content is not None:
            ret = task_router.change_content_function(task_data.__dict__['content'].__dict__, instance)
            return Response(ret)

        return Response({'status': 'success'})
