from collections.abc import Callable
from typing import NamedTuple, Iterable

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import QuerySet, Q
from rest_framework import serializers

from tasks.models import Task, TaskStatus, TaskProperties, TaskBaseModel

User = get_user_model()


class RouterTask(NamedTuple):
    task: type(Task)
    create_function: Callable[[Iterable[dict[str, str]], type(User) | None], Iterable[str]] | None
    read_serializer: type(serializers.Serializer)
    write_serializer: type(serializers.Serializer)
    content_model: type(TaskBaseModel) | None
    change_content_function: Callable[[dict[str, str], type(Task)], [str]] | None = None
    answer_serializer: type(serializers.Serializer) | None = None


class RouterContent(NamedTuple):
    content_model: type(models.Model)
    object_model: type(models.Model)
    object_key_name: str
    serializer: type(serializers.Serializer)


def change_task_properties(instance: Task, properties: TaskProperties) -> None:
    """ Сохраняет свойства инстанса из базового класса: статус, флаги выгрузки... """
    keys = set(instance.__dict__.keys()) & set(properties.__dict__.keys())
    if not len(keys):
        return None

    fields = {key: str(properties.__dict__[key]) for key in keys if properties.__dict__[key] is not None}
    type(instance).objects.filter(pk=instance.pk).update(**fields)


def get_task_queryset(task: Task, filter_task: dict[str: str]) -> QuerySet:
    """ Получает выборку из стандартного менеджера модели и сериализатор по типу задачи из роутера.
     В роутере содержатся модели наследуемые от Task """
    transform_incoming_data(filter_task)
    queryset = task.objects.all()

    class_keys = set(dir(task)) | {'not_closed', 'only_close', 'all_users'}
    filter_keys = set(filter_task.keys())

    if len(filter_keys.difference(class_keys)):
        raise TaskException

    if filter_task.get('all_users'):
        filter_task.pop('user')
        filter_task.pop('all_users')
    elif filter_task.get('only_close'):
        queryset = queryset.filter(status=TaskStatus.CLOSE)
        filter_task.pop('only_close')
    else:
        queryset = queryset.filter(Q(user=filter_task['user']) | Q(status=TaskStatus.NEW))

    if filter_task.get('not_closed'):
        queryset = queryset.exclude(status=TaskStatus.CLOSE).exclude(closed=True)
        filter_task.pop('not_closed')

    if filter_task.get('user') is not None:
        filter_task.pop('user')

    if len(filter_task):
        queryset = queryset.filter(**filter_task)

    return queryset


def get_content_queryset(router: RouterContent, type_task: str, filter_object: dict[str: str]) -> QuerySet:
    """ Получает данные объектов по модели object_model из роутера. Фильтрация по любому полю модели объекта.
     Дополнительный фильтр по типу задания: класс - content_model """
    transform_incoming_data(filter_object)
    objects_queryset = router.object_model.objects.all()
    class_keys = set(dir(router.object_model))
    filter_keys = set(filter_object.keys())
    if len(filter_keys.difference(class_keys)):
        raise TaskException

    if len(filter_keys):
        objects_queryset = objects_queryset.filter(**filter_object)

    object_ids = objects_queryset.values_list('pk', flat=True)
    content_filter = {router.object_key_name + '__in': list(object_ids),
                      'type_operation': type_task.upper()}
    filtered_ids = router.content_model.objects.filter(**content_filter).values_list(*(router.object_key_name,),
                                                                                     flat=True)
    objects_queryset = objects_queryset.filter(pk__in=list(filtered_ids))
    return objects_queryset


def transform_incoming_data(request_params: dict[str:str]) -> None:
    for key, value in request_params.items():
        if str(value).capitalize() == 'True' or str(value).capitalize() == 'False':
            request_params[key] = str(value).capitalize()


class TaskException(Exception):
    """ Не возможно сформировать список заданий """
    pass
