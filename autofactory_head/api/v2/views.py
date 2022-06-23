from json import JSONDecodeError

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

import api.views
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
            content = task_router.content_model(**request.data)
        except TypeError:
            raise APIException('Переданы некорректные данные')
        except JSONDecodeError:
            raise APIException('Переданы некорректные данные')

        if content.properties is not None:
            change_task_properties(instance, content.__dict__['properties'])

        ret = task_router.change_content_function(content.__dict__['content'].__dict__, instance)
        return Response(ret)
