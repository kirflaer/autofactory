from django.contrib.auth import get_user_model
from django.db import models
from catalogs.models import Device, Line, ExternalSource
from factory_core.models import OperationBaseModel, ExternalSystemExchangeMixin, Shift
from catalogs.models import Product, Organization, Direction, Client

User = get_user_model()


class MarkingOperation(OperationBaseModel, ExternalSystemExchangeMixin):
    """ Операция маркировки """
    author = models.ForeignKey(User, on_delete=models.SET_NULL,
                               verbose_name='Автор', null=True)

    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, verbose_name='Организация', blank=True,
                                     null=True)

    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name='Устройство', null=True, blank=True)
    manual_editing = models.BooleanField(default=False)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки')
    weight = models.FloatField('Вес', default=0)

    line = models.ForeignKey(Line, on_delete=models.SET_NULL, verbose_name='Линия', blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Номенклатура', blank=True, null=True)
    group = models.UUIDField('Группа', blank=True, null=True)
    group_offline = models.CharField('Ключ группы оффлайн', blank=True, null=True, max_length=10)
    is_offline_operation = models.BooleanField('Оффлайн операция', default=False)
    closing_date = models.DateTimeField('Дата закрытия', blank=True, null=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, verbose_name='Смена', blank=True, null=True)

    class Meta:
        verbose_name = 'Операция маркировки'
        verbose_name_plural = 'Операции маркировки'


class MarkingOperationMark(models.Model):
    operation = models.ForeignKey(MarkingOperation, on_delete=models.CASCADE, related_name='marks')
    mark = models.CharField('Марка', max_length=500)
    encoded_mark = models.CharField('Зашифрованная марка', max_length=500, null=True)
    aggregation_code = models.CharField('Код агрегации', max_length=500, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Номенклатура', blank=True, null=True)
    scan_date = models.DateTimeField('Время сканирования', blank=True, null=True)

    class Meta:
        verbose_name = 'Марка'
        verbose_name_plural = 'Марки'


class RawMark(models.Model):
    operation = models.ForeignKey(MarkingOperation, on_delete=models.CASCADE, related_name='raw_marks')
    mark = models.CharField(max_length=500)

    class Meta:
        verbose_name = 'Необработанная марка'
        verbose_name_plural = 'Необработанные марки'
