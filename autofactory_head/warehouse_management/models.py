import uuid

from django.contrib.auth import get_user_model
from django.db import models

from catalogs.models import Product, Storage
from factory_core.models import BaseModel
from tasks.models import Task

User = get_user_model()


class PalletStatus(models.TextChoices):
    COLLECTED = 'COLLECTED'
    CONFIRMED = 'CONFIRMED'
    POSTED = 'POSTED'
    SHIPPED = 'SHIPPED'


class Pallet(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)
    id = models.CharField('Идентификатор', max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Номенклатура', blank=True,
                                null=True)
    creation_date = models.DateTimeField('Дата создания', auto_now_add=True)
    collector = models.ForeignKey(User, verbose_name='Сборщик', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField('Статус', max_length=20, choices=PalletStatus.choices, default=PalletStatus.COLLECTED)
    weight = models.FloatField('Вес', default=0)
    content_count = models.PositiveIntegerField('Количество позиций внутри паллеты', default=0)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки', blank=True, null=True)

    class Meta:
        verbose_name = 'Паллета'
        verbose_name_plural = 'Паллеты'

    def __str__(self):
        return self.id


class PalletContent(models.Model):
    pallet = models.ForeignKey('Pallet', on_delete=models.CASCADE,
                               related_name='codes', verbose_name='Паллета')
    aggregation_code = models.CharField('Код агрегации', max_length=500)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Номенклатура', blank=True,
                                null=True)

    class Meta:
        verbose_name = 'Код агрегации'
        verbose_name_plural = 'Коды агрегации'

    def __str__(self):
        return f'{self.pallet} - {self.aggregation_code}'


class BaseOperation(BaseModel, Task):
    class Meta:
        abstract = True


class MovementOperation(BaseOperation):
    type_task = 'PRODUCT_MOVEMENT'
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Склад')
    production_date = models.DateField('Дата выработки', blank=True, null=True)

    class Meta:
        verbose_name = 'Перемещение товаров'
        verbose_name_plural = 'Операции перемещения товаров'


class PalletCollectOperation(BaseOperation):
    type_task = 'PALLET_COLLECT'

    class Meta:
        verbose_name = 'Сбор паллет'
        verbose_name_plural = 'Операции сбора паллет'


class ManyToManyOperationMixin(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)
    operation = models.UUIDField('ГУИД операции', null=True)
    type_operation = models.CharField('Тип операции', max_length=100, null=True)
    number_operation = models.CharField('Номер операции', max_length=100, null=True)
    external_source = models.CharField('Наименование внешнего источника', max_length=100, null=True)

    class Meta:
        abstract = True

    def fill_properties(self, operation: BaseOperation) -> None:
        self.operation = operation.guid
        self.type_operation = operation.type_task
        self.number_operation = operation.number
        self.external_source = None if operation.external_source is None else operation.external_source.name
        self.save()


class OperationPallet(ManyToManyOperationMixin):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета')

    class Meta:
        verbose_name = 'Паллета операции'
        verbose_name_plural = 'Паллеты операций'


class OperationProduct(ManyToManyOperationMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Номенклатура')
    weight = models.FloatField('Вес', default=0.0)
    count = models.PositiveIntegerField('Количество', default=0.0)

    class Meta:
        verbose_name = 'Номенклатура операции'
        verbose_name_plural = 'Номенклатура операций'
