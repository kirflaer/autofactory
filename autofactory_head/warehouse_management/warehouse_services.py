import uuid
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum
from dateutil import parser
from rest_framework.exceptions import APIException

from catalogs.models import ExternalSource, Product, Storage, Direction, Client
from factory_core.models import Shift
from tasks.models import TaskStatus, Task
from warehouse_management.models import (AcceptanceOperation, Pallet, OperationBaseOperation, OperationPallet,
                                         OperationProduct, PalletCollectOperation,
                                         PlacementToCellsOperation,
                                         OperationCell,
                                         MovementBetweenCellsOperation, ShipmentOperation, OrderOperation,
                                         PalletContent, PalletProduct, PalletSource, ArrivalAtStockOperation,
                                         InventoryOperation, PalletStatus, TypeCollect, SelectionOperation, StorageCell,
                                         StorageCellContentState, StatusCellContent, RepackingOperation)

User = get_user_model()


def enrich_pallet_info(validated_data: dict, product_keys: list, instance: Pallet) -> None:
    if validated_data.get('sources') is not None:
        sources = validated_data.pop('sources')
        for source in sources:
            pallet_source = Pallet.objects.select_for_update().filter(guid=source['pallet_source']).first()
            if pallet_source is None:
                raise APIException('Не найдена паллета источник')

            if pallet_source.content_count < source['count']:
                raise APIException('Не хватает коробок в паллете источнике')

            pallet_source.content_count -= source['count']
            pallet_source.weight -= source['weight']
            if pallet_source.content_count == 0:
                pallet_source.status = PalletStatus.ARCHIVED
            if pallet_source.weight < 0:
                pallet_source.weight = 0
            pallet_source.save()

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
                pallet_product_string.save()


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
        order = OrderOperation.objects.get(guid=order_guid)
        order.close()


@transaction.atomic
def create_inventory_with_placement_operation(serializer_data: dict[str: str], user: User) -> Iterable[str]:
    """ Создает операцию отгрузки со склада"""
    instance = InventoryOperation.objects.create(user=user, status=TaskStatus.CLOSE)
    pallet = Pallet.objects.get(guid=serializer_data['pallet'])
    if pallet.content_count != serializer_data['count']:
        pallet.content_count = serializer_data['count']
        pallet.save()

    cell = StorageCell.objects.get(external_key=serializer_data['cell'])
    operation_pallets = OperationCell.objects.create(pallet=pallet, cell_source=cell)
    operation_pallets.fill_properties(instance)
    StorageCellContentState.objects.create(cell=cell, pallet=pallet)
    instance.close()
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
        direction = Direction.objects.filter(external_key=element['direction']).first()
        operation = ShipmentOperation.objects.create(user=user, direction=direction, external_source=external_source)

        _create_child_task_shipment(element['pallets'], user, operation, TypeCollect.SHIPMENT)
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
                raise APIException('Не найдена зависимая паллета')
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
def create_movement_cell_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения между ячейками"""
    result = []
    for element in serializer_data:
        operation = MovementBetweenCellsOperation.objects.create(ready_to_unload=True, closed=True,
                                                                 status=TaskStatus.CLOSE)
        fill_operation_cells(operation, element['cells'])
        result.append(operation.guid)
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
        if len(pallets) == 1 and pallets[0].shift is not None:
            operation.ready_to_unload = False
            operation.save()
        result.append(operation.guid)
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
    """ Создает операцию приенмки товаров. Возвращает идентификаторы внешнего источника """

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
def create_pallets(serializer_data: Iterable[dict[str: str]], user: User | None = None, task: Task | None = None) -> \
        list[Pallet]:
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
            element['product'] = Product.objects.filter(guid=product).first()

            if not element.get('cell'):
                cell = None
            else:
                cell = element['cell']
            element['cell'] = StorageCell.objects.filter(guid=cell).first()

            if not element.get('production_shop'):
                production_shop = None
            else:
                production_shop = element['production_shop']
            element['production_shop'] = Storage.objects.filter(guid=production_shop).first()

            if element.get('code_offline') is not None:
                element['marking_group'] = element['code_offline']

            if element.get('shift') is not None:
                shift = Shift.objects.filter(pk=element.get('shift')).first()
                element['shift'] = shift
                element['marking_group'] = shift.guid

            serializer_keys = set(element.keys())
            class_keys = set(dir(Pallet))
            [serializer_keys.discard(field) for field in related_tables]
            fields = {key: element[key] for key in (class_keys & serializer_keys)}
            pallet = Pallet.objects.create(**fields)

        if element.get('products') is not None:
            products_count = PalletProduct.objects.filter(pallet=pallet).count()
            if not products_count:
                for product in element['products']:
                    product['pallet'] = pallet
                    product['product'] = Product.objects.filter(external_key=product['product']).first()

                    if product.get('order_external_source') is not None:
                        order = create_order_operation(product, user, task)
                        product.pop('order_external_source')
                        product['order'] = order

                    PalletProduct.objects.create(**product)

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
