from django.db import models
from django.db.models import Max

from catalogs.models import Device, Line
from factory_core.models import BaseModel
from catalogs.models import Product


class MarkingOperation(BaseModel):
    device = models.ForeignKey(Device, on_delete=models.CASCADE,
                               verbose_name='Устройство', null=True,
                               blank=True, )
    manual_editing = models.BooleanField(default=False)
    batch_number = models.CharField(max_length=150,
                                    verbose_name='Номер партии', blank=True,
                                    null=True)
    production_date = models.DateField('Дата выработки')

    line = models.ForeignKey(Line, on_delete=models.CASCADE,
                             verbose_name='Линия', blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура', blank=True,
                                null=True)

    def get_query_set(self):
        return MarkingOperation.objects.all()


class MarkingOperationMark(models.Model):
    operation = models.ForeignKey(MarkingOperation, on_delete=models.CASCADE,
                                  related_name='marks')
    mark = models.CharField(max_length=500)
    encoded_mark = models.CharField(max_length=500, null=True)
    aggregation_code = models.CharField(max_length=500, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура', blank=True,
                                null=True)


class RawMark(models.Model):
    operation = models.ForeignKey(MarkingOperation, on_delete=models.CASCADE,
                                  related_name='raw_marks')
    mark = models.CharField(max_length=500)


class CollectingOperation(BaseModel):
    identifier = models.CharField(verbose_name='Идентификатор', blank=True,
                                  null=True,
                                  max_length=50)

    def get_query_set(self):
        return CollectingOperation.objects.all()


class CollectCode(models.Model):
    operation = models.ForeignKey(CollectingOperation,
                                  on_delete=models.CASCADE,
                                  related_name='codes')
    code = models.CharField(max_length=500)
