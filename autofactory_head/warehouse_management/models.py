import uuid
from typing import List

from django.contrib.auth import get_user_model
from django.db import models
from pydantic.dataclasses import dataclass

from catalogs.models import Product, Storage, StorageCell, Direction, Client
from factory_core.models import OperationBaseModel
from tasks.models import Task, TaskBaseModel

User = get_user_model()


class PalletStatus(models.TextChoices):
    COLLECTED = 'COLLECTED'
    CONFIRMED = 'CONFIRMED'
    POSTED = 'POSTED'
    SHIPPED = 'SHIPPED'
    ARCHIVE = 'ARCHIVE'
    WAIT = 'WAIT'


class Pallet(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)
    id = models.CharField('Идентификатор', max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Номенклатура', blank=True,
                                null=True)
    creation_date = models.DateTimeField('Дата создания', auto_now_add=True)
    collector = models.ForeignKey(User, verbose_name='Сборщик', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField('Статус', max_length=20, choices=PalletStatus.choices, default=PalletStatus.COLLECTED)
    weight = models.IntegerField('Вес', default=0)
    content_count = models.PositiveIntegerField('Количество позиций внутри паллеты', default=0)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки', blank=True, null=True)
    external_key = models.CharField(max_length=36, blank=True, null=True, verbose_name='Внешний ключ')

    class Meta:
        verbose_name = 'Паллета'
        verbose_name_plural = 'Паллеты'

    def __str__(self):
        return self.id


class PalletContent(models.Model):
    pallet = models.ForeignKey('Pallet', on_delete=models.CASCADE,
                               related_name='codes', verbose_name='Паллета')
    aggregation_code = models.CharField('Код агрегации', max_length=500)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Номенклатура', blank=True, null=True)

    class Meta:
        verbose_name = 'Код агрегации'
        verbose_name_plural = 'Коды агрегации'

    def __str__(self):
        return f'{self.pallet} - {self.aggregation_code}'


class PalletProduct(models.Model):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета', related_name='products')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, verbose_name='Номенклатура', null=True, blank=True)
    weight = models.FloatField('Вес', default=0.0)
    count = models.PositiveIntegerField('Количество', default=0.0)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки', blank=True, null=True)

    class Meta:
        verbose_name = 'Номенклатура паллеты'
        verbose_name_plural = 'Номенклатура паллет'


class PalletSource(models.Model):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета', related_name='sources')
    pallet_source = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета источник')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, verbose_name='Номенклатура', null=True, blank=True)
    weight = models.FloatField('Вес', default=0.0)
    count = models.PositiveIntegerField('Количество', default=0.0)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки', blank=True, null=True)

    class Meta:
        verbose_name = 'Паллета источник'
        verbose_name_plural = 'Паллеты источники'


class OperationBaseOperation(OperationBaseModel, Task):
    class Meta:
        abstract = True

    def close(self):
        self.ready_to_unload = True
        super().close()


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
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Склад')
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
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Размещение в ячейки'
        verbose_name_plural = 'Операции размещения в ячейки'


class MovementBetweenCellsOperation(OperationBaseOperation):
    type_task = 'MOVEMENT_BETWEEN_CELLS'
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Перемещение между ячейками'
        verbose_name_plural = 'Операции перемещения между ячейками'


class ShipmentOperation(OperationBaseOperation):
    type_task = 'SHIPMENT'
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name='Направление')

    class Meta:
        verbose_name = 'Отгрузка со склада'
        verbose_name_plural = 'Операции отгрузки со склада'


class OrderOperation(OperationBaseOperation):
    type_task = 'ORDER'
    parent_task = models.ForeignKey(ShipmentOperation, on_delete=models.CASCADE, verbose_name='Родительское задание',
                                    null=True,
                                    blank=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Клиент')

    class Meta:
        verbose_name = 'Заказ клиента'
        verbose_name_plural = 'Заказы клиентов'

    def close(self):
        super().close()
        open_orders_count = OrderOperation.objects.filter(parent_task=self.parent_task, closed=False).exclude(
            guid=self.guid).count()
        if not open_orders_count:
            self.parent_task.close()


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
