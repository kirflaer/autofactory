from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.db.models import Max
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
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
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
    number = models.IntegerField(default=1)
    is_new = models.BooleanField(default=True, verbose_name='Это новый')

    def __str__(self):
        return f'{self.number} - {self.date.strftime("%d.%m.%Y %H:%M:%S")}'

    def close(self):
        self.closed = True
        self.save()

    @classmethod
    def get_query_set(cls):
        return None

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.is_new:
            qs = self.get_query_set()
            if qs is None:
                number = 1
            else:
                number = qs.aggregate(Max('number')).get('number__max')
                if number is None:
                    number = 1
                else:
                    number += 1

            self.number = number
            self.is_new = False
        super().save(force_insert, force_update, using, update_fields)
