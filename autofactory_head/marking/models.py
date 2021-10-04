from django.db import models
from catalogs.models import Device
from factory_core.models import BaseModel, ShiftOperation
from catalogs.models import Product


class DeviceSignal(models.Model):
    date = models.DateTimeField('Дата записи', auto_now_add=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date']


class RawMark(models.Model):
    date = models.DateTimeField('Дата записи', auto_now_add=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    mark = models.CharField(max_length=500)


class MarkingOperation(BaseModel):
    shift = models.ForeignKey(ShiftOperation, on_delete=models.CASCADE)
    manual_editing = models.BooleanField(default=False)


class MarkingOperationMarks(BaseModel):
    operation = models.ForeignKey(MarkingOperation, on_delete=models.CASCADE,
                                  related_name='marks')
    mark = models.CharField(max_length=500)
    encoded_mark = models.CharField(max_length=500, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура', blank=True,
                                null=True)
