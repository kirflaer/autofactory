from django.db import models
import uuid


class BaseModel(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=1024)
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class BaseExternalModel(BaseModel):
    class Meta:
        abstract = True

    external_key = models.CharField(max_length=36, blank=True,
                                    verbose_name='Внешний ключ')


class Organization(BaseExternalModel):
    pass


class Storage(BaseExternalModel):
    pass


class Department(BaseExternalModel):
    pass


class Device(BaseExternalModel):
    polling_interval = models.PositiveIntegerField(
        verbose_name='Интервал опроса')


class Line(BaseModel):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True,
                               blank=True, verbose_name='Устройство')
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True,
                                blank=True, verbose_name='Склад')
    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                                   null=True,
                                   blank=True, verbose_name='Подразделение')


class Product(BaseExternalModel):
    gtin = models.CharField(verbose_name='GTIN', max_length=200, default='',
                            blank=True)
    vendor_code = models.CharField(verbose_name='Артикул', max_length=50,
                                   default='', blank=True)
    sku = models.CharField(default='', blank=True, max_length=50)
    expiration_date = models.PositiveIntegerField(verbose_name='Срок годности',
                                                  default=0)
    count_in_pallet = models.PositiveIntegerField(
        verbose_name='Количество в паллете', default=0)
