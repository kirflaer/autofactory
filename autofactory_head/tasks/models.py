from django.contrib.auth import get_user_model
from django.db import models

from catalogs.models import ExternalSource
from factory_core.models import ExternalSystemExchangeMixin

User = get_user_model()


class TaskStatus(models.TextChoices):
    NEW = 'NEW'
    WORK = 'WORK'
    CLOSE = 'CLOSE'


class Task(ExternalSystemExchangeMixin):
    type_task = models.CharField(max_length=255, verbose_name='Тип задания')

    parent_task = models.ForeignKey('self', on_delete=models.CASCADE,
                                    verbose_name='Родительское задание',
                                    null=True,
                                    blank=True)

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
