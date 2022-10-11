import uuid
from typing import List

from django.contrib.auth import get_user_model
from django.db import models
from pydantic.dataclasses import dataclass

from catalogs.models import Product, Storage, StorageCell, Direction, Client
from factory_core.models import OperationBaseModel
from tasks.models import Task, TaskBaseModel, TaskStatus

User = get_user_model()


class PalletStatus(models.TextChoices):
    COLLECTED = 'COLLECTED'
    CONFIRMED = 'CONFIRMED'
    POSTED = 'POSTED'
    SHIPPED = 'SHIPPED'
    ARCHIVED = 'ARCHIVED'
    WAITED = 'WAITED'
    FOR_SHIPMENT = 'FOR_SHIPMENT'


class PalletType(models.TextChoices):
    SHIPPED = 'SHIPPED'
    FULLED = 'FULLED'
    COMBINED = 'COMBINED'


class Pallet(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)
    id = models.CharField('Идентификатор', max_length=50, blank=True, default='')
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
    production_shop = models.ForeignKey(Storage, on_delete=models.CASCADE, verbose_name='Цех производства', blank=True,
                                        null=True)
    pallet_type = models.CharField('Тип', max_length=50, choices=PalletType.choices, default=PalletType.FULLED)
    marking_group = models.CharField('Группа маркировки', blank=True, null=True, max_length=36)

    class Meta:
        verbose_name = 'Паллета'
        verbose_name_plural = 'Паллеты'

    def __str__(self):
        return f'{self.status} / {self.batch_number} / {self.id} / {self.guid}'


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
    type_operation = models.CharField('Тип операции', max_length=100)
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
    count_fact = models.PositiveIntegerField('Количество факт (для операций сбора)', default=0.0)

    class Meta:
        verbose_name = 'Номенклатура операции'
        verbose_name_plural = 'Номенклатура операций'


class OperationCell(ManyToManyOperationMixin):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета', null=True, blank=True)
    cell_source = models.ForeignKey(StorageCell, on_delete=models.CASCADE, verbose_name='Складская ячейка',
                                    related_name='operation_cell')
    cell_destination = models.ForeignKey(StorageCell, on_delete=models.SET_NULL, null=True, blank=True,
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
        verbose_name_plural = 'Приемка товаров (Заказ на перемещение)'


class PlacementToCellsOperation(OperationBaseOperation):
    type_task = 'PLACEMENT_TO_CELLS'
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Размещение в ячейки'
        verbose_name_plural = 'Размещения в ячейки'


class MovementBetweenCellsOperation(OperationBaseOperation):
    type_task = 'MOVEMENT_BETWEEN_CELLS'
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Перемещение между ячейками'
        verbose_name_plural = 'Перемещения между ячейками'


class ShipmentOperation(OperationBaseOperation):
    type_task = 'SHIPMENT'
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name='Направление')

    class Meta:
        verbose_name = 'Отгрузка со склада'
        verbose_name_plural = 'Отгрузка со со склада (Заявка на завод)'


class PalletCollectOperation(OperationBaseOperation):
    type_task = 'PALLET_COLLECT'
    parent_task = models.ForeignKey(ShipmentOperation, on_delete=models.CASCADE, verbose_name='Родительское задание',
                                    null=True,
                                    blank=True)

    SHIPMENT = 'SHIPMENT'
    ACCEPTANCE = 'ACCEPTANCE'

    TYPE_COLLECT = ((SHIPMENT, SHIPMENT), (ACCEPTANCE, ACCEPTANCE),)
    type_collect = models.CharField('Тип сбора', max_length=255, choices=TYPE_COLLECT, default=ACCEPTANCE)

    class Meta:
        verbose_name = 'Сбор паллет'
        verbose_name_plural = 'Сбор паллет'

    def close(self):
        super().close()
        open_task_count = PalletCollectOperation.objects.filter(parent_task=self.parent_task, closed=False).exclude(
            guid=self.guid).count()
        if not open_task_count:
            self.parent_task.status = TaskStatus.CLOSE
            self.parent_task.close()


class OrderOperation(OperationBaseOperation):
    type_task = 'ORDER'
    parent_task = models.ForeignKey(ShipmentOperation, on_delete=models.CASCADE, verbose_name='Родительское задание',
                                    null=True,
                                    blank=True)

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Клиент')
    client_presentation = models.CharField('Клиент', max_length=150, blank=True, null=True, default='')

    class Meta:
        verbose_name = 'Заказ клиента'
        verbose_name_plural = 'Отгрузка со склада (Заказы клиентов)'

    def close(self):
        super().close()
        open_orders_count = OrderOperation.objects.filter(parent_task=self.parent_task, closed=False).exclude(
            guid=self.guid).count()
        if not open_orders_count:
            self.parent_task.status = TaskStatus.CLOSE
            self.parent_task.close()


class PalletProduct(models.Model):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета', related_name='products')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, verbose_name='Номенклатура', null=True, blank=True)
    weight = models.FloatField('Вес', default=0.0)
    count = models.PositiveIntegerField('Количество', default=0.0)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки', blank=True, null=True)
    order = models.ForeignKey(OrderOperation, verbose_name='Заказ клиента', blank=True, null=True,
                              on_delete=models.SET_NULL)
    external_key = models.CharField(max_length=36, blank=True, null=True, verbose_name='Внешний ключ')
    has_shipped_products = models.BooleanField('Содержит номенклатуру требующую обеспечения', default=False)
    is_collected = models.BooleanField('Собрано', default=False)

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
    external_key = models.CharField(max_length=36, blank=True, null=True, verbose_name='Внешний ключ')
    order = models.ForeignKey(OrderOperation, verbose_name='Заказ клиента', blank=True, null=True,
                              on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Паллета источник'
        verbose_name_plural = 'Паллеты источники'


class ArrivalAtStockOperation(OperationBaseOperation):
    type_task = 'ARRIVAL_AT_STOCK'
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Приход на склад'
        verbose_name_plural = 'Приход на склад (Поступление товаров и услуг)'


class InventoryOperation(OperationBaseOperation):
    type_task = 'INVENTORY'

    class Meta:
        verbose_name = 'Инвентаризация'
        verbose_name_plural = 'Инвентаризация'


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


@dataclass
class ProductContent:
    plan: int
    fact: int
    product: str


@dataclass
class InventoryTaskContent:
    products: List[ProductContent]


class InventoryTask(TaskBaseModel):
    content: InventoryTaskContent
