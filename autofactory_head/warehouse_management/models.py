import datetime
import uuid
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.db import models
from pydantic.dataclasses import dataclass

from catalogs.models import Product, Storage, Direction, Client, BaseExternalModel
from factory_core.signals import operation_pre_close
from factory_core.models import OperationBaseModel, Shift
from tasks.models import Task, TaskBaseModel, TaskStatus

User = get_user_model()


class PalletStatus(models.TextChoices):
    NEW = 'NEW'
    COLLECTED = 'COLLECTED'
    CONFIRMED = 'CONFIRMED'
    POSTED = 'POSTED'
    SHIPPED = 'SHIPPED'
    ARCHIVED = 'ARCHIVED'
    WAITED = 'WAITED'
    FOR_SHIPMENT = 'FOR_SHIPMENT'
    SELECTED = 'SELECTED'
    PLACED = 'PLACED'
    FOR_REPACKING = 'FOR_REPACKING'
    FOR_PLACED = 'FOR_PLACED'
    PRE_FOR_SHIPMENT = 'PRE_FOR_SHIPMENT'


class PalletType(models.TextChoices):
    SHIPPED = 'SHIPPED'
    FULLED = 'FULLED'
    COMBINED = 'COMBINED'
    REPACKING = 'REPACKING'


class TypeCollect(models.TextChoices):
    SHIPMENT = 'SHIPMENT'
    ACCEPTANCE = 'ACCEPTANCE'
    SELECTION = 'SELECTION'
    WRITE_OFF = 'WRITE_OFF'
    INVENTORY = 'INVENTORY'
    DIVIDED = 'DIVIDED'


class CellAreaIdentifier(models.TextChoices):
    FOR_SHIPMENT = 'FOR_SHIPMENT'
    REPLACEMENT = 'REPLACEMENT'


class StatusCellContent(models.TextChoices):
    PLACED = 'PLACED'
    REMOVED = 'REMOVED'


@dataclass
class CellContent:
    cell_source: str
    cell_destination: str


@dataclass
class PlacementToCellsContent:
    cells: List[CellContent]


class PlacementToCellsTask(TaskBaseModel):
    content: Optional[PlacementToCellsContent] = None


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


class StorageArea(BaseExternalModel):
    new_status_on_admission = models.CharField('Статус', max_length=20, choices=PalletStatus.choices,
                                               default=PalletStatus.SELECTED)
    use_for_automatic_placement = models.BooleanField('Используется для автоматического размещения', default=False)
    allow_movement = models.BooleanField('Разрешить перемещение между ячейками', default=False)

    class Meta:
        verbose_name = 'Область хранения'
        verbose_name_plural = 'Области хранения'


class StorageCell(BaseExternalModel):
    barcode = models.CharField('Штрихкод', max_length=100, default='-')
    storage_area = models.ForeignKey(StorageArea, verbose_name='Область хранения', null=True, blank=True,
                                     on_delete=models.SET_NULL)
    needed_scan = models.BooleanField('Необходимо сканировать при размещении', default=True)
    needed_filter_by_task = models.BooleanField('Необходим фильтр по задания при размещении', default=False)
    rack_number = models.PositiveIntegerField('Номер стеллажа', default=0, blank=True)
    position = models.PositiveIntegerField('Позиция внутри стеллажа', default=0, blank=True)
    id_area = models.CharField(
        verbose_name='Идентификатор области',
        max_length=20,
        choices=CellAreaIdentifier.choices,
        null=True,
        blank=False
    )

    class Meta:
        verbose_name = 'Складская ячейка'
        verbose_name_plural = 'Складские ячейки'


class Pallet(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)
    id = models.CharField('Идентификатор', max_length=50, blank=True, default='')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Номенклатура', blank=True,
                                null=True)
    creation_date = models.DateTimeField('Дата создания', auto_now_add=True)
    collector = models.ForeignKey(User, verbose_name='Сборщик', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField('Статус', max_length=20, choices=PalletStatus.choices, default=PalletStatus.NEW)
    weight = models.IntegerField('Вес', default=0)
    content_count = models.PositiveIntegerField('Количество позиций внутри паллеты', default=0)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки', blank=True, null=True)
    external_key = models.CharField(max_length=36, blank=True, null=True, verbose_name='Внешний ключ')
    production_shop = models.ForeignKey(Storage, on_delete=models.CASCADE, verbose_name='Цех производства', blank=True,
                                        null=True)
    pallet_type = models.CharField('Тип', max_length=50, choices=PalletType.choices, default=PalletType.FULLED)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, verbose_name='Смена', blank=True, null=True)

    # Для совместимости со второй версией везде будет записываться guid смены (shift)
    marking_group = models.CharField('Группа маркировки', blank=True, null=True, max_length=36)
    not_fully_collected = models.BooleanField('Собрана не полностью', default=False, blank=True, null=True)

    external_task_key = models.CharField('Ключ внешнего задания', blank=True, null=True, max_length=36)

    name = models.CharField('Наименование', blank=True, null=True, max_length=155)
    consignee = models.CharField('Грузополучатель', blank=True, null=True, max_length=155)
    series = models.CharField('Серия', blank=True, null=True, max_length=155)
    group = models.CharField('Группа паллет', blank=True, null=True, max_length=36)
    initial_count = models.PositiveIntegerField('Исходное количество ящиков', null=True, default=0)

    class Meta:
        verbose_name = 'Паллета'
        verbose_name_plural = 'Паллеты'

    def __str__(self):
        if not self.name:
            return f'{self.status} / {self.batch_number} / {self.id} / {self.guid}'
        else:
            return f'{self.name} / {self.consignee}'


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
        operation_pre_close.send(sender=self.__class__, instance=self)
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
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета',
                               related_name='operation_pallets')
    dependent_pallet = models.ForeignKey(Pallet, on_delete=models.SET_NULL, blank=True, null=True,
                                         verbose_name='Зависимая паллета', related_name='depended_pallets')
    count = models.PositiveIntegerField('Количество', default=0, blank=True)

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
                                         verbose_name='Ячейка (назначение / измененная)')

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

    def close(self):
        # Находим сборы паллет по разделенным ОБП паллетам и закрываем меняем статус по ним
        operations = list(PalletCollectOperation.objects.filter(parent_task=self.guid, status=TaskStatus.WORK))
        for operation in operations:
            operation.status = TaskStatus.CLOSE
            operation.close()
        super().close()


class StorageCellContentState(models.Model):
    creating_date = models.DateTimeField('Дата создания', auto_now_add=True)
    cell = models.ForeignKey(StorageCell, verbose_name='Ячейка', on_delete=models.CASCADE)
    pallet = models.ForeignKey(Pallet, verbose_name='Паллета', on_delete=models.CASCADE)
    status = models.CharField('Статус', max_length=20, choices=StatusCellContent.choices,
                              default=StatusCellContent.PLACED)

    class Meta:
        verbose_name = 'Состояние складских ячеек'
        verbose_name_plural = 'Состояние складских ячеек'


class PlacementToCellsOperation(OperationBaseOperation):
    type_task = 'PLACEMENT_TO_CELLS'
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Размещение в ячейки'
        verbose_name_plural = 'Размещения в ячейки'

    def close(self):
        cells = OperationCell.objects.filter(operation=self.guid)
        for row in cells:
            cell = row.cell_source if not row.cell_destination else row.cell_destination
            StorageCellContentState.objects.create(pallet=row.pallet, cell=cell)
            if row.pallet.status == PalletStatus.CONFIRMED:
                row.pallet.status = PalletStatus.PLACED
                row.pallet.save()
        super().close()


class MovementBetweenCellsOperation(OperationBaseOperation):
    type_task = 'MOVEMENT_BETWEEN_CELLS'
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Склад')

    class Meta:
        verbose_name = 'Перемещение между ячейками'
        verbose_name_plural = 'Перемещения между ячейками'


class ShipmentOperation(OperationBaseOperation):
    type_task = 'SHIPMENT'
    has_selection = models.BooleanField('Есть отбор', default=False, blank=True, null=True)
    manager = models.CharField('Менеджер', blank=True, null=True, max_length=155)
    direction = models.CharField('Направление', blank=True, null=True, max_length=155)
    car_carrier = models.CharField('Машина перевозчик', blank=True, null=True, max_length=155)

    class Meta:
        verbose_name = 'Отгрузка со склада'
        verbose_name_plural = 'Отгрузка со склада (Заявка на завод)'


class SelectionOperation(OperationBaseOperation):
    type_task = 'SELECTION'
    parent_task = models.ForeignKey(ShipmentOperation, on_delete=models.CASCADE, verbose_name='Родительское задание',
                                    null=True,
                                    blank=True)

    class Meta:
        verbose_name = 'Отбор со склада'
        verbose_name_plural = 'Отбор со склада (Заявка на завод)'


class PalletCollectOperation(OperationBaseOperation):
    PARENT_TASK_TYPES = {'SHIPMENT': ShipmentOperation,
                         'SELECTION': SelectionOperation}

    type_task = 'PALLET_COLLECT'
    parent_task = models.CharField('Родительское задание', null=True, blank=True, max_length=36)

    type_collect = models.CharField('Тип сбора', max_length=255, choices=TypeCollect.choices,
                                    default=TypeCollect.ACCEPTANCE)

    class Meta:
        verbose_name = 'Сбор паллет'
        verbose_name_plural = 'Сбор паллет'

    def close(self):
        super().close()
        if self.parent_task is None or not self.PARENT_TASK_TYPES.get(self.type_collect):
            return

        open_task_count = PalletCollectOperation.objects.filter(parent_task=self.parent_task, closed=False).exclude(
            guid=self.guid).count()

        if not open_task_count:
            instance = self.PARENT_TASK_TYPES[self.type_collect].objects.get(guid=self.parent_task)
            instance.status = TaskStatus.CLOSE
            instance.close()

        if self.type_collect == TypeCollect.SHIPMENT:
            orders = OrderOperation.objects.filter(parent_task=self.parent_task)
            not_collected_orders = (
                PalletProduct.objects.filter(
                    order__in=orders,
                    is_collected=False
                )
                .values_list('order', flat=True)
            )

            for order in orders:
                if order.guid in not_collected_orders:
                    continue
                order.close()


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
    has_divergence = models.BooleanField('Имеет расхождение', default=False)
    series = models.CharField('Серия', blank=True, null=True, max_length=155)

    class Meta:
        verbose_name = 'Номенклатура паллеты'
        verbose_name_plural = 'Номенклатура паллет'

    def __str__(self):
        return f'{self.order} / {self.product} / {self.count}'


class PalletSource(models.Model):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета', related_name='sources',
                               null=True)
    pallet_source = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name='Паллета источник')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, verbose_name='Номенклатура', null=True, blank=True)
    weight = models.FloatField('Вес', default=0.0)
    count = models.PositiveIntegerField('Количество', default=0.0)
    batch_number = models.CharField('Номер партии', max_length=150, blank=True, null=True)
    production_date = models.DateField('Дата выработки', blank=True, null=True)
    external_key = models.CharField(max_length=36, blank=True, null=True, verbose_name='Внешний ключ')
    order = models.ForeignKey(OrderOperation, verbose_name='Заказ клиента', blank=True, null=True,
                              on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Пользователь')
    additional_collect = models.BooleanField('Дополнение к заданию', blank=True, default=False)
    type_collect = models.CharField('Тип сбора', max_length=255, choices=TypeCollect.choices,
                                    default=TypeCollect.SHIPMENT)
    related_task = models.CharField('Идентификатор связанного задания', max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

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

    def close(self):
        super().close()

        rows = OperationCell.objects.filter(operation=self.guid)
        for row in rows:
            Pallet.objects.filter(guid=row.pallet.guid).update(status=PalletStatus.PLACED)
            StorageCellContentState.objects.create(cell=row.cell_source, pallet=row.pallet)


class RepackingOperation(OperationBaseOperation):
    type_task = 'REPACKING'

    class Meta:
        verbose_name = 'Переупаковка'
        verbose_name_plural = 'Переупаковка'


class SuitablePallets(models.Model):
    pallet_product = models.ForeignKey(PalletProduct, verbose_name='Строка товаров', on_delete=models.CASCADE)
    pallet = models.ForeignKey(Pallet, verbose_name='Паллета', on_delete=models.CASCADE)
    count = models.PositiveIntegerField('Количество')
    priority = models.PositiveIntegerField('Приоритет')

    class Meta:
        verbose_name = 'Подходящие паллеты'
        verbose_name_plural = 'Подходящие паллеты (построчная выгрузка)'


class WriteOffOperation(OperationBaseOperation):
    type_task = 'WRITE_OFF'
    comment = models.CharField('Комментарий', max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = 'Списание продукции'
        verbose_name_plural = 'Списание продукции'


class InventoryAddressWarehouseContent(ManyToManyOperationMixin):
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE, verbose_name='Номенклатура')
    pallet = models.ForeignKey(to=Pallet, on_delete=models.CASCADE, verbose_name='Паллета')
    cell = models.ForeignKey(to=StorageCell, on_delete=models.CASCADE, verbose_name='Складская ячейка')
    plan = models.PositiveIntegerField('Количество (план)', default=0.0)
    fact = models.PositiveIntegerField('Количество (факт)', default=0.0)
    priority = models.PositiveIntegerField('Приоритет сортировки', default=0)

    class Meta:
        verbose_name = 'Инвентаризация адресного склада (Содержимое операции)'
        verbose_name_plural = 'Инвентаризация адресного склада (Содержимое операции)'


class InventoryAddressWarehouseOperation(OperationBaseOperation):
    type_task = 'INVENTORY_ADDRESS_WAREHOUSE'

    class Meta:
        verbose_name = 'Инвентаризация адресного склада'
        verbose_name_plural = 'Инвентаризация адресного склада'


class CancelShipmentOperation(OperationBaseOperation):
    type_task = 'CANCEL_SHIPMENT'

    class Meta:
        verbose_name = 'Отмена отгрузки'
        verbose_name_plural = 'Отмена отгрузки'

    def close(self):
        operations = OperationCell.objects.filter(operation=self.guid)
        for operation in operations:
            operation.pallet.status = PalletStatus.PLACED
            operation.pallet.save()
            cell = operation.cell_source if not operation.cell_destination else operation.cell_destination
            StorageCellContentState.objects.create(pallet=operation.pallet, cell=cell)
        super().close()


class MovementShipmentOperation(OperationBaseOperation):

    type_task = 'MOVEMENT_WITH_SHIPMENT'

    class Meta:
        verbose_name = 'Перемещение под отгрузку'
        verbose_name_plural = 'Перемещения под отгрузку'
