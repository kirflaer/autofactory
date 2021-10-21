from django.db import models
import uuid

from django.db.models import UniqueConstraint


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


class Device(BaseModel):
    AUTO_SCANNER = 'AUTO_SCANNER'
    TABLET = 'TABLET'
    DCT = 'DCT'

    MODE = (
        (AUTO_SCANNER, AUTO_SCANNER),
        (TABLET, TABLET),
        (DCT, DCT),
    )

    mode = models.CharField(max_length=255, choices=MODE, default=DCT)

    identifier = models.CharField(verbose_name='IP', blank=True, null=True,
                                  max_length=50)
    port = models.PositiveIntegerField(blank=True, null=True)
    polling_interval = models.PositiveIntegerField(
        verbose_name='Интервал опроса', blank=True, null=True)


class Product(BaseExternalModel):
    gtin = models.CharField(default='', blank=True, max_length=50)
    expiration_date = models.PositiveIntegerField('Срок годности', default=0)


class Line(BaseModel):
    devices = models.ManyToManyField(Device,
                                     through='LineDevice')
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True,
                                blank=True, verbose_name='Склад')
    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                                   null=True,
                                   blank=True, verbose_name='Подразделение')
    products = models.ManyToManyField(Product,
                                      through='LineProduct')


class LineDevice(models.Model):
    line = models.ForeignKey(Line, on_delete=models.CASCADE, null=True,
                             blank=True,
                             verbose_name='Линия')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True,
                               blank=True,
                               verbose_name='Устройство')

    class Meta:
        constraints = [UniqueConstraint(fields=['line', 'device'],
                                        name='unique_devices')]


class LineProduct(models.Model):
    line = models.ForeignKey(Line, on_delete=models.CASCADE, null=True,
                             blank=True,
                             verbose_name='Линия')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True,
                                blank=True,
                                verbose_name='Номенклатура')

    class Meta:
        constraints = [UniqueConstraint(fields=['line', 'product'],
                                        name='unique_products')]


class Unit(BaseExternalModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура',
                                related_name='units')
    count_in_pallet = models.PositiveIntegerField('Количество в паллете',
                                                  default=0)

    capacity = models.PositiveIntegerField('Вместимость', default=0)
    is_default = models.BooleanField('Упаковка по умолчанию', default=False)
