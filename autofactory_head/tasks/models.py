from django.contrib.auth import get_user_model
from django.db import models
from pydantic.main import BaseModel

from catalogs.models import ExternalSource
from factory_core.models import ExternalSystemExchangeMixin

User = get_user_model()


class TaskStatus(models.TextChoices):
    NEW = 'NEW'
    WORK = 'WORK'
    WAIT = 'WAIT'
    CLOSE = 'CLOSE'


class Task(ExternalSystemExchangeMixin):
    type_task = models.CharField(max_length=255, verbose_name='Тип задания')

    status = models.CharField(max_length=255, choices=TaskStatus.choices, default=TaskStatus.NEW,
                              verbose_name='Статус')

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь', null=True,
                             blank=True)

    external_source = models.ForeignKey(ExternalSource,
                                        on_delete=models.CASCADE,
                                        verbose_name='Внешний источник',
                                        null=True,
                                        blank=True)

    class Meta:
        abstract = True


class TaskProperties(BaseModel):
    status: TaskStatus | None
    unloaded: bool | None


class TaskBaseModel(BaseModel):
    properties: TaskProperties | None
    content: BaseModel | None
