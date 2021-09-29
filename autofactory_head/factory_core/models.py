from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from catalogs.models import Organization, Product, Line

User = get_user_model()


class BaseModel(models.Model):
    class Meta:
        abstract = True

    date = models.DateTimeField('Дата создания', auto_now_add=True)
    guid = models.UUIDField(unique=True, default=uuid.uuid4,
                            editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор', null=True)

    def __str__(self):
        return f'{self.pk} - {self.date}'


class ShiftOperation(BaseModel):
    class TypeOfShift(models.TextChoices):
        MOVING = 'MV', _('Перемещение')
        MARKING = 'MR', _('Маркировка')
        INVENTORY = 'IV', _('Инвентаризация')

    type_of_shift = models.CharField(
        max_length=2,
        choices=TypeOfShift.choices,
        default=TypeOfShift.MARKING,
    )

    closed = models.BooleanField(default=False, verbose_name='Закрыта')
    unloaded = models.BooleanField(default=False, verbose_name='Выгружена')
    batch_number = models.CharField(max_length=150,
                                    verbose_name='Номер партии', blank=True,
                                    null=True)
    production_date = models.DateField('Дата выработки')

    line = models.ForeignKey(Line, on_delete=models.CASCADE,
                             verbose_name='Линия', blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура', blank=True,
                                null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     verbose_name='Организация', blank=True,
                                     null=True)
