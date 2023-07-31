from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum
from dateutil import parser
from rest_framework.exceptions import APIException

from api.exceptions import BadRequest
from catalogs.models import ExternalSource, Product, Storage, Unit
from factory_core.models import Shift
from tasks.models import TaskStatus, Task
from warehouse_management.models import (
    AcceptanceOperation, Pallet, OperationBaseOperation, OperationPallet, OperationProduct, PalletCollectOperation,
    PlacementToCellsOperation, OperationCell, MovementBetweenCellsOperation, ShipmentOperation, OrderOperation,
    PalletContent, PalletProduct, PalletSource, ArrivalAtStockOperation, InventoryOperation, PalletStatus, TypeCollect,
    SelectionOperation, StorageCell, StorageCellContentState, StatusCellContent, RepackingOperation, SuitablePallets
)

User = get_user_model()


def enrich_pallet_info(validated_data: dict, product_keys: list, instance: Pallet) -> None:
    if validated_data.get('sources') is not None:
        sources = validated_data.pop('sources')
        for source in sources:
            pallet_source = Pallet.objects.filter(guid=source['pallet_source']).first()
            if pallet_source is None:
                raise APIException('Не найдена паллета источник')

            if pallet_source.content_count < source['count']:
                raise APIException('Не хватает коробок в паллете источнике')

            remove_boxes_from_pallet(pallet_source, source['count'], source.get('weight'))

            source['pallet_source'] = Pallet.objects.filter(guid=source['pallet_source']).first()
            source['pallet'] = instance
            source['product'] = Product.objects.filter(guid=source['product']).first()

            PalletSource.objects.create(**source)
            product_keys.append(source['external_key'])

    if validated_data.get('collected_strings') is not None:
        collected_strings = validated_data.pop('collected_strings')
        product_keys += collected_strings
        for string in collected_strings:
            pallet_product_string = PalletProduct.objects.filter(external_key=string).first()
            if pallet_product_string is not None:
                pallet_product_string.is_collected = True
                pallet_product_string.has_divergence = True
                pallet_product_string.save()


def remove_boxes_from_pallet(pallet: Pallet, count: int, weight: int | None = None) -> None:
    pallet.content_count -= count

    if weight is not None:
        pallet.weight -= weight

    if pallet.content_count == 0:
        pallet.status = PalletStatus.ARCHIVED
        cell_state = get_cell_state(pallet=pallet)
        if cell_state is not None and cell_state.status == StatusCellContent.PLACED:
            StorageCellContentState.objects.create(cell=cell_state.cell, pallet=pallet,
                                                   status=StatusCellContent.REMOVED)

    if pallet.weight < 0:
        pallet.weight = 0
    pallet.save()


def check_and_collect_orders(product_keys: list[str]):
    """ Функция проверяет все ли данные по заказам собраны. Если сбор окончен закрывает заказы """
    sources = PalletSource.objects.filter(external_key__in=product_keys).values('external_key').annotate(Sum('count'))
    pallet_products = PalletProduct.objects.filter(external_key__in=product_keys)
    orders = pallet_products.values_list('order', flat=True)
    order_products = pallet_products.values('order', 'external_key').annotate(Sum('count'))

    for product in order_products:
        if not sources.filter(external_key=product['external_key'], count__sum__gte=product['count__sum']).exists():
            continue
        order_product = PalletProduct.objects.get(external_key=product['external_key'])
        order_product.is_collected = True
        order_product.save()

    not_collected_orders = PalletProduct.objects.filter(order__in=orders, is_collected=False).values_list('order',
                                                                                                          flat=True)
    for order_guid in orders:
        if order_guid in not_collected_orders:
            continue
        order = OrderOperation.objects.filter(guid=order_guid).first()
        if not order:
            raise APIException(f'Не найден заказ {order_guid} операция отменена')
        order.close()


@transaction.atomic
def create_inventory_with_placement_operation(serializer_data: dict[str: str], user: User) -> Iterable[str]:
    """ Создает операцию отгрузки со склада"""
    instance = InventoryOperation.objects.create(user=user, ready_to_unload=True)
    pallet = Pallet.objects.get(guid=serializer_data['pallet'])
    pallet.status = PalletStatus.FOR_PLACED

    if pallet.content_count != serializer_data['count']:
        pallet.content_count = serializer_data['count']

    if serializer_data.get('weight') is not None and pallet.weight != serializer_data.get('weight'):
        pallet.weight = serializer_data.get('weight')
    pallet.save()

    cell = StorageCell.objects.get(external_key=serializer_data['cell'])
    operation_pallets = OperationCell.objects.create(pallet=pallet, cell_source=cell)
    operation_pallets.fill_properties(instance)

    return instance.guid


@transaction.atomic
def create_shipment_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию отгрузки со склада"""
    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        task = ShipmentOperation.objects.filter(external_source=external_source).first()
        if task is not None:
            result.append(task.guid)
            continue

        pallets = element.pop('pallets')
        cells = element.pop('cells')
        element.pop('external_source')

        operation = ShipmentOperation.objects.create(external_source=external_source, **element)

        _create_child_task_shipment(pallets, user, operation, TypeCollect.SHIPMENT)
        fill_operation_cells(operation, cells)
        result.append(operation.guid)
    return result


@transaction.atomic
def create_selection_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию отбора со склада"""
    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        task = SelectionOperation.objects.filter(external_source=external_source).first()
        if task is not None:
            result.append(task.guid)
            continue
        operation = SelectionOperation.objects.create(external_source=external_source)

        fill_operation_cells(operation, element['cells'])
        result.append(operation.guid)
    return result


@transaction.atomic
def create_repacking_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию переупаковки"""
    result = []
    for row in serializer_data:
        external_source = get_or_create_external_source(row)
        task = RepackingOperation.objects.filter(external_source=external_source).first()
        if task is not None:
            result.append(task.guid)
            continue
        operation = RepackingOperation.objects.create(external_source=external_source)
        result.append(operation.guid)
        for pallet_data in row['pallets']:
            dependent_pallet = Pallet.objects.filter(id=pallet_data['pallet']).first()
            if not dependent_pallet:
                raise APIException(f'Не найдена зависимая паллета {pallet_data["pallet"]}')
            pallet = Pallet.objects.create(product=dependent_pallet.product,
                                           batch_number=dependent_pallet.batch_number,
                                           production_date=dependent_pallet.production_date)
            operation_pallets = OperationPallet.objects.create(pallet=pallet, dependent_pallet=dependent_pallet,
                                                               count=pallet_data['count'])
            operation_pallets.fill_properties(operation)
    return result


def _create_child_task_shipment(pallets_data: Iterable[dict[str: str]], user: User, operation: Task,
                                type_collect: TypeCollect) -> None:
    """ Создает операцию отгрузки либо отбора с дочерней операцией сбора паллет со склада"""
    pallets = create_pallets(pallets_data, user, operation)
    for pallet in pallets:
        child_operation = PalletCollectOperation.objects.create(type_collect=type_collect,
                                                                parent_task=operation.pk)
        fill_operation_pallets(child_operation, (pallet,))


@transaction.atomic
def create_order_operation(serializer_data: dict[str: str], user: User,
                           parent_task: ShipmentOperation) -> OrderOperation:
    """ Создает заказ клиента"""
    client_presentation = serializer_data['order_external_source'].pop('client_presentation')
    external_source = get_or_create_external_source(serializer_data, 'order_external_source')
    task = OrderOperation.objects.filter(external_source=external_source).first()
    if task is not None:
        return task
    return OrderOperation.objects.create(user=user, client_presentation=client_presentation,
                                         external_source=external_source, parent_task=parent_task)


@transaction.atomic
def create_movement_cell_operation(serializer_data: dict[str: str], user: User) -> Iterable[str]:
    """ Создает операцию перемещения между ячейками"""
    pallet = Pallet.objects.get(id=serializer_data['pallet'])
    cell_destination = StorageCell.objects.get(guid=serializer_data['cell_destination'])

    if cell_destination.storage_area is None:
        raise APIException('Отсутствует складское помещение у ячейки назначения.')

    if not (pallet.status in (PalletStatus.FOR_REPACKING, PalletStatus.FOR_SHIPMENT,
                              PalletStatus.PLACED) and cell_destination.storage_area.allow_movement):
        raise BadRequest('Перемещение недоступно.')

    result = []

    operation = MovementBetweenCellsOperation.objects.create(ready_to_unload=True, closed=True,
                                                             status=TaskStatus.CLOSE)

    cells = [{
        'cell': serializer_data['cell_source'],
        'cell_destination': serializer_data['cell_destination'],
        'pallet': serializer_data['pallet']
    }]

    fill_operation_cells(operation, cells)
    result.append(operation.guid)
    change_cell_content_state(serializer_data, pallet)

    return result


@transaction.atomic
def create_placement_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию размещение в ячейках"""
    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        task = PlacementToCellsOperation.objects.filter(external_source=external_source).first()
        if task is not None:
            continue
        storage = Storage.objects.filter(external_key=element['storage']).first()
        operation = PlacementToCellsOperation.objects.create(storage=storage, external_source=external_source)
        fill_operation_cells(operation, element['cells'])

        result.append(operation.guid)
    return result


@transaction.atomic
def create_collect_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения"""
    result = []
    for element in serializer_data:
        operation = PalletCollectOperation.objects.create(closed=True, status=TaskStatus.CLOSE, user=user,
                                                          ready_to_unload=True)
        pallets = create_pallets(element['pallets'])
        fill_operation_pallets(operation, pallets)
        if len(pallets) == 1 and pallets[0].shift is not None and not pallets[0].shift.closed:
            operation.ready_to_unload = False
            operation.save()
        result += pallets
    return result


@transaction.atomic
def create_acceptance_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения. Возвращает идентификаторы внешнего источника """

    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        result.append(external_source.external_key)
        operation = AcceptanceOperation.objects.filter(external_source=external_source).first()
        if operation is not None:
            continue

        storage = Storage.objects.filter(external_key=element['storage']).first()
        operation = AcceptanceOperation.objects.create(external_source=external_source, storage=storage,
                                                       batch_number=element['batch_number'],
                                                       production_date=parser.parse(element['production_date']))
        fill_operation_pallets(operation, element['pallets'])
        fill_operation_products(operation, element['products'])

    return result


@transaction.atomic
def create_arrival_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию приемки товаров. Возвращает идентификаторы внешнего источника """

    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        result.append(external_source.external_key)
        operation = ArrivalAtStockOperation.objects.filter(external_source=external_source).first()
        if operation is not None:
            continue

        storage = Storage.objects.filter(external_key=element['storage']).first()
        operation = ArrivalAtStockOperation.objects.create(external_source=external_source, storage=storage)
        fill_operation_products(operation, element['products'])

    return result


@transaction.atomic
def create_inventory_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию инвентаризации товаров. Возвращает идентификаторы внешнего источника """

    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        result.append(external_source.external_key)
        operation = InventoryOperation.objects.filter(external_source=external_source).first()
        if operation is not None:
            continue

        operation = InventoryOperation.objects.create(external_source=external_source)
        fill_operation_products(operation, element['products'])

    return result


@transaction.atomic
def create_pallets(
        serializer_data: Iterable[dict[str: str]],
        user: User | None = None,
        task: Task | None = None
) -> list[Pallet]:
    """ Создает паллету и наполняет ее кодами агрегации"""
    result = []
    related_tables = ('codes', 'products')

    for element in serializer_data:
        search_field = 'id' if element.get('id') is not None else 'external_key'
        search_value = element.get(search_field)
        pallet = None

        if search_value is not None:
            pallet_filter = {search_field: search_value}
            pallet = Pallet.objects.filter(**pallet_filter).first()

        if not pallet:
            if not element.get('product'):
                product = None
            else:
                product = element['product']
            element['product'] = Product.objects.filter(Q(guid=product) | Q(external_key=product)).first()

            if element['product'] and not element['product'].variable_pallet_weight:
                unit = Unit.objects.filter(is_default=True, product=element['product']).first()

                if unit and element.get('content_count'):
                    element['weight'] = element['content_count'] * unit.weight

            if not element.get('cell'):
                cell = None
            else:
                cell = element['cell']
            element['cell'] = StorageCell.objects.filter(guid=cell).first()

            if not element.get('production_shop'):
                production_shop = None
            else:
                production_shop = element['production_shop']
            element['production_shop'] = Storage.objects.filter(
                Q(guid=production_shop) | Q(external_key=production_shop)
            ).first()

            if element.get('code_offline') is not None:
                element['marking_group'] = element['code_offline']

            if element.get('shift') is not None:
                shift = Shift.objects.filter(pk=element.get('shift')).first()
                element['shift'] = shift
                element['marking_group'] = shift.guid

            if element.get('content_count'):
                element['initial_count'] = element['content_count']

            serializer_keys = set(element.keys())
            class_keys = set(dir(Pallet))
            [serializer_keys.discard(field) for field in related_tables]
            fields = {key: element[key] for key in (class_keys & serializer_keys)}
            pallet = Pallet.objects.create(**fields)

        if element.get('products') is not None:
            products_count = PalletProduct.objects.filter(pallet=pallet).count()
            if not products_count:
                suitable_pallets = None
                for product in element['products']:
                    product['pallet'] = pallet
                    product['product'] = Product.objects.filter(external_key=product['product']).first()

                    if product.get('order_external_source') is not None:
                        order = create_order_operation(product, user, task)
                        product.pop('order_external_source')
                        product['order'] = order

                    if product.get('suitable_pallets') is not None:
                        suitable_pallets = product.pop('suitable_pallets')

                    pallet_product = PalletProduct.objects.create(**product)
                    if suitable_pallets is not None:
                        for suitable_pallet_row in suitable_pallets:
                            pallet_id = suitable_pallet_row.pop('id')
                            suitable_pallet = Pallet.objects.filter(id=pallet_id).first()
                            if suitable_pallet is None:
                                raise APIException(f'Не найдена паллета {pallet_id} в блоке построчной выгрузке')
                            SuitablePallets.objects.create(pallet_product=pallet_product, pallet=suitable_pallet,
                                                           **suitable_pallet_row)

        if element.get('codes') is not None:
            for code in element['codes']:
                aggregation_code = PalletContent.objects.filter(aggregation_code=code).first()
                if aggregation_code is not None:
                    continue
                PalletContent.objects.create(pallet=pallet, aggregation_code=aggregation_code, product=pallet.product)

        result.append(pallet)

    return result


def fill_operation_products(operation: OperationBaseOperation, raw_data: Iterable[dict[str: str]]) -> None:
    """ Заполняет товары абстрактной операции """

    for task_product in raw_data:
        product = Product.objects.filter(external_key=task_product['product']).first()
        if product is None:
            continue

        weight = 0 if task_product.get('weight') is None else task_product['weight']
        count = 0 if task_product.get('count') is None else task_product['count']
        operation_products = OperationProduct.objects.create(product=product, weight=weight, count=count)
        operation_products.fill_properties(operation)


def fill_operation_pallets(operation: OperationBaseOperation, raw_data: Iterable[str | Pallet]) -> None:
    """ Заполняет информацию о паллетах абстрактной операции """

    for pallet_instance in raw_data:
        if isinstance(pallet_instance, Pallet):
            pallet = pallet_instance
        else:
            pallet = Pallet.objects.filter(id=pallet_instance).first()
        if pallet is None:
            continue
        operation_pallets = OperationPallet.objects.create(pallet=pallet)
        operation_pallets.fill_properties(operation)


def fill_operation_cells(operation: OperationBaseOperation, raw_data: Iterable[dict[str: str]]) -> None:
    """ Заполняет ячейки абстрактной операции """

    for element in raw_data:
        cell = StorageCell.objects.filter(Q(external_key=element['cell']) | Q(guid=element['cell'])).first()
        if cell is None:
            continue

        if element.get('cell_destination') is not None:
            cell_destination = StorageCell.objects.filter(
                Q(external_key=element['cell_destination']) | Q(guid=element['cell_destination'])).first()
        else:
            cell_destination = None

        if element.get('pallet') is not None:
            pallet = Pallet.objects.filter(id=element['pallet']).first()

            if pallet is not None and not pallet.series and element.get('series') is not None:
                pallet.series = element.get('series')
                pallet.save()
        else:
            pallet = None
        operation_cell = OperationCell.objects.create(cell_source=cell, cell_destination=cell_destination,
                                                      pallet=pallet)
        operation_cell.fill_properties(operation)


def get_or_create_external_source(raw_data=dict[str: str], field_name='external_source') -> ExternalSource:
    """ Создает либо находит элемент таблицы внешнего источника """

    external_source = ExternalSource.objects.filter(
        external_key=raw_data[field_name]['external_key']).first()
    if external_source is None:
        external_source = ExternalSource.objects.create(**raw_data[field_name])
    return external_source


@transaction.atomic
def change_content_placement_operation(content: dict[str: str], instance: PlacementToCellsOperation) -> str:
    """ Изменяет содержимое операции размещение в ячейках"""
    for element in content['cells']:
        cell_row = OperationCell.objects.filter(operation=instance.guid,
                                                cell_source__external_key=element.cell_source).first()
        if cell_row is None:
            continue

        cell_row.cell_destination = StorageCell.objects.filter(external_key=element.cell_destination).first()
        cell_row.save()
    return instance.guid


@transaction.atomic
def change_content_inventory_operation(content: dict[str: str], instance: InventoryOperation) -> str:
    """ Изменяет содержимое строки товаров для инвентаризации"""
    for element in content["products"]:
        product_row = OperationProduct.objects.filter(operation=instance.guid, product__guid=element.product,
                                                      count=element.plan).first()
        if product_row is None:
            continue

        product_row.count_fact = element.fact
        product_row.save()
    return instance.guid


@transaction.atomic
def change_cell_content_state(content: dict[str: str], pallet: Pallet) -> str:
    """ Меняет расположение паллеты в ячейке. Возвращает статус из области новой ячейки """
    cell_source = StorageCell.objects.get(guid=content['cell_source'])
    cell_destination = StorageCell.objects.get(guid=content['cell_destination'])

    StorageCellContentState.objects.create(cell=cell_source, pallet=pallet, status=StatusCellContent.REMOVED)
    StorageCellContentState.objects.create(cell=cell_destination, pallet=pallet)

    new_status = cell_destination.storage_area.new_status_on_admission
    pallet.status = new_status
    pallet.save()

    return new_status


def get_cell_state(**kwargs) -> StorageCellContentState | None:
    filter_kwargs = kwargs.copy()
    filter_kwargs['status'] = StatusCellContent.PLACED

    if not StorageCellContentState.objects.filter(**filter_kwargs).exists():
        return None

    change_state_row = StorageCellContentState.objects.filter(**filter_kwargs).latest('creating_date')
    filter_kwargs.pop('status')
    last_state_row = StorageCellContentState.objects.filter(**filter_kwargs).latest('creating_date')
    if change_state_row.pk != last_state_row.pk:
        return None

    return last_state_row


def get_pallet_filter_from_shipment(shipment_external_key: str) -> dict[str, list] | None:
    external_source = ExternalSource.objects.filter(external_key=shipment_external_key).first()
    if not external_source:
        return None
    operation = ShipmentOperation.objects.filter(external_source=external_source).first()
    if not operation:
        return None

    cells = OperationCell.objects.filter(operation=operation.guid).values_list('pallet__guid', flat=True)

    return {'guid__in': list(cells)}


def get_unused_cells_for_placement() -> list[StorageCell]:
    """ Возвращает список не занятых ячеек для автоматического размещения """

    inventory_ids = list(InventoryOperation.objects.all().values_list('guid', flat=True))
    used_cells = OperationCell.objects.filter(operation__in=inventory_ids).values_list('cell_source__guid', flat=True)
    cells = StorageCell.objects.filter(storage_area__use_for_automatic_placement=True).exclude(guid__in=used_cells)

    result = []
    for cell in cells:
        state = get_cell_state(cell=cell)
        if not state or state.status == StatusCellContent.REMOVED:
            result.append(cell)

    return result


def get_pallets_in_acceptance(value: str) -> dict[str, list] | None:
    """ Получает паллеты находящие в незакрытых заданиях на приемку """
    operations = list(AcceptanceOperation.objects.exclude(status=TaskStatus.CLOSE).values_list('guid', flat=True))
    pallets = OperationPallet.objects.filter(operation__in=operations).values_list('pallet__guid', flat=True)
    return {'guid__in': list(pallets)}
