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

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.is_new:
            number = MarkingOperation.objects.all().aggregate(
                Max('number')).get('number__max')
            if number is None:
                number = 1
            else:
                number += 1

            self.number = number
            self.is_new = False
        super().save(force_insert, force_update, using, update_fields)


class MarkingOperationMarks(models.Model):
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
