from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from catalogs.models import Organization, Product, Line

User = get_user_model()


class BaseModel(models.Model):
    """ Базовая модель для операций
    Во внешнюю систему отправляются все ready_to_unload
    После выгрузки внешним запросом помечаются unloaded"""

    class Meta:
        abstract = True

    date = models.DateTimeField('Дата создания', auto_now_add=True)
    guid = models.UUIDField(unique=True, default=uuid.uuid4,
                            editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор', null=True)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     verbose_name='Организация', blank=True,
                                     null=True)

    closed = models.BooleanField(default=False,
                                 verbose_name='Закрыта')

    unloaded = models.BooleanField(default=False, verbose_name='Выгружена')
    ready_to_unload = models.BooleanField(default=False,
                                          verbose_name='Готова к выгрузке')

    def __str__(self):
        return f'{self.pk} - {self.date.strftime("%d.%m.%Y %H:%M:%S")}'

    def close(self):
        self.closed = True
        self.save()


