import datetime
from random import randrange
import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Max

from catalogs.models import Line, Product

User = get_user_model()


class TypeShift(models.TextChoices):
    MARKED = 'MARKED'
    UNMARKED = 'UNMARKED'
    SEMI_PRODUCTS = 'SEMI_PRODUCTS'


class ExternalSystemExchangeMixin(models.Model):
    """Расширение для моделей добавляющие возможность контролировать статус обмена
    Во внешнюю систему отправляются все ready_to_unload
    После выгрузки внешним запросом помечаются unloaded"""

    unloaded = models.BooleanField(default=False, verbose_name='Выгружена')
    ready_to_unload = models.BooleanField(default=False,
                                          verbose_name='Готова к выгрузке')

    external_source = models.CharField(max_length=255,
                                       verbose_name='Источник внешней системы',
                                       blank=True)
    closed = models.BooleanField(default=False,
                                 verbose_name='Закрыта')

    class Meta:
        abstract = True

    def close(self):
        self.closed = True
        self.save()


class OperationBaseModel(models.Model):
    """ Базовая модель для операций """

    number = models.IntegerField(default=1)
    date = models.DateTimeField('Дата создания', auto_now_add=True)
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.number} - {self.date.strftime("%d.%m.%Y %H:%M:%S")}'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.date is None:
            qs = type(self).objects.all()
            number = qs.aggregate(Max('number')).get('number__max') or 0
            self.number = number + 1

        super().save(force_insert, force_update, using, update_fields)


class Shift(models.Model):
    """ Смена """
    creating_date = models.DateTimeField('Дата создания', auto_now_add=True)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки')
    closing_date = models.DateTimeField('Дата закрытия', blank=True, null=True)
    line = models.ForeignKey(Line, on_delete=models.SET_NULL, verbose_name='Линия', blank=True, null=True)
    guid = models.UUIDField('ГУИД', primary_key=True, default=uuid.uuid4, editable=False)
    code_offline = models.CharField('Ключ группы оффлайн', blank=True, null=True, max_length=10)
    closed = models.BooleanField('Закрыта', default=False)
    number = models.PositiveIntegerField('Номер', default=0)
    author = models.ForeignKey(User, verbose_name='Автор', on_delete=models.SET_NULL, blank=True, null=True)
    type = models.CharField('Тип', max_length=20, choices=TypeShift.choices, default=TypeShift.MARKED, null=True)

    class Meta:
        verbose_name = 'Смена'
        verbose_name_plural = 'Смены'

    def __str__(self):
        return f'{self.batch_number} - {self.production_date} - {self.line}'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.creating_date is None:
            number = Shift.objects.aggregate(Max('number')).get('number__max') or 0
            self.number = number + 1

        if self.code_offline is None:
            self.code_offline = str(randrange(100, 900, 1))

        if self.closed and not self.closing_date:
            self.closing_date = datetime.datetime.now(datetime.timezone.utc)
        super().save(force_insert, force_update, using, update_fields)


class ShiftProduct(models.Model):
    shift = models.ForeignKey(Shift, verbose_name='Смена', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='Номенклатура', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Номенклатура смен'
        verbose_name_plural = 'Номенклатура смен'
