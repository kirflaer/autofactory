from collections.abc import Callable
from typing import NamedTuple, Iterable

from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Q
from rest_framework import serializers

from tasks.models import Task, TaskStatus, TaskProperties, TaskBaseModel

User = get_user_model()


class RouterContent(NamedTuple):
    task: type(Task)
    create_function: Callable[[Iterable[dict[str, str]], type(User) | None], Iterable[str]]
    read_serializer: type(serializers.Serializer)
    write_serializer: type(serializers.Serializer)
    content_model: type(TaskBaseModel) | None
    change_content_function: Callable[[dict[str, str], type(Task)], [str]] | None


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
    queryset = task.objects.all()

    class_keys = set(dir(task)) | {'not_closed', 'only_close'}
    filter_keys = set(filter_task.keys())

    if len(filter_keys.difference(class_keys)):
        raise TaskException

    if filter_task.get('not_closed'):
        queryset = queryset.exclude(status=TaskStatus.CLOSE, closed=True)
        filter_task.pop('not_closed')
    elif filter_task.get('only_close'):
        queryset = queryset.filter(status=TaskStatus.CLOSE, closed=True)
        filter_task.pop('only_close')
    else:
        queryset = queryset.filter(Q(user=filter_task['user']) | Q(status=TaskStatus.NEW))
        filter_task.pop('user')

    if filter_task.get('user') is not None:
        filter_task.pop('user')
    if len(filter_task):
        queryset = queryset.filter(**filter_task)

    return queryset


class TaskException(Exception):
    """ Не возможно сформировать список заданий """
