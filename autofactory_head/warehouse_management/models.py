import uuid
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.db import models
from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from catalogs.models import Product, Storage, StorageCell
from factory_core.models import OperationBaseModel
from tasks.models import Task, TaskProperties, TaskBaseModel

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


class OperationBaseOperation(OperationBaseModel, Task):
    class Meta:
        abstract = True


class ManyToManyOperationMixin(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)
    operation = models.UUIDField('ГУИД операции', null=True)
    type_operation = models.CharField('Тип операции', max_length=100, null=True)
    number_operation = models.CharField('Номер операции', max_length=100, null=True)
    external_source = models.CharField('Наименование внешнего источника', max_length=100, null=True)

    class Meta:
        abstract = True

    def fill_properties(self, operation: OperationBaseOperation) -> None:
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


class OperationCell(OperationProduct):
    cell = models.ForeignKey(StorageCell, on_delete=models.CASCADE, verbose_name='Складская ячейка',
                             related_name='operation_cell')
    changed_cell = models.ForeignKey(StorageCell, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Измененная ячейка')

    class Meta:
        verbose_name = 'Складские ячейки операции'
        verbose_name_plural = 'Складские ячейки операций'


class AcceptanceOperation(OperationBaseOperation):
    type_task = 'ACCEPTANCE_TO_STOCK'
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Склад')
    production_date = models.DateField('Дата выработки', blank=True, null=True)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)

    class Meta:
        verbose_name = 'Приемка на склад'
        verbose_name_plural = 'Операции приемки товаров'




class PalletCollectOperation(OperationBaseOperation):
    type_task = 'PALLET_COLLECT'

    class Meta:
        verbose_name = 'Сбор паллет'
        verbose_name_plural = 'Операции сбора паллет'


class PlacementToCellsOperation(OperationBaseOperation):
    type_task = 'PLACEMENT_TO_CELLS'
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Размещение в ячейки'
        verbose_name_plural = 'Операции размещения в ячейки'


class MovementBetweenCellsOperation(OperationBaseOperation):
    type_task = 'MOVEMENT_BETWEEN_CELLS'
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Перемещение между ячейками'
        verbose_name_plural = 'Операции перемещения между ячейками'


@dataclass
class CellContent:
    cell: str
    changed_cell: str
    product: str


@dataclass
class PlacementToCellsContent:
    cells: List[CellContent]


class PlacementToCellsTask(TaskBaseModel):
    content: PlacementToCellsContent
