import uuid
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Sum
from dateutil import parser
from catalogs.models import ExternalSource, Product, Storage, StorageCell, Direction, Client
from tasks.models import TaskStatus, Task
from warehouse_management.models import (AcceptanceOperation, Pallet, OperationBaseOperation, OperationPallet,
                                         OperationProduct, PalletCollectOperation,
                                         PlacementToCellsOperation,
                                         OperationCell,
                                         MovementBetweenCellsOperation, ShipmentOperation, OrderOperation,
                                         PalletContent, PalletProduct, PalletSource)

User = get_user_model()


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

    order_need_close = PalletProduct.objects.filter(order__in=orders).exclude(is_collected=False).values_list('order',
                                                                                                              flat=True)
    for order_guid in order_need_close:
        order = OrderOperation.objects.get(guid=order_guid)
        order.close()


@transaction.atomic
def create_shipment_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию отгрузки со склада"""
    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        task = ShipmentOperation.objects.filter(external_source=external_source).first()
        if task is not None:
            continue
        direction = Direction.objects.filter(external_key=element['direction']).first()
        operation = ShipmentOperation.objects.create(user=user, direction=direction, external_source=external_source)

        pallets = create_pallets(element['pallets'], user, operation)
        for pallet in pallets:
            child_operation = PalletCollectOperation.objects.create(user=user,
                                                                    type_collect=PalletCollectOperation.SHIPMENT,
                                                                    parent_task=operation)
            fill_operation_pallets(child_operation, (pallet,))

        result.append(operation.guid)
    return result


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
        operation = PalletCollectOperation.objects.create(closed=True, status=TaskStatus.CLOSE, user=user)
        pallets = create_pallets(element['pallets'])
        fill_operation_pallets(operation, pallets)
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

            if not element.get('production_shop'):
                production_shop = None
            else:
                production_shop = element['production_shop']
            element['production_shop'] = Storage.objects.filter(guid=production_shop).first()

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

        product = Pallet.objects.filter(Q(external_key=element['pallet']) | Q(guid=element['pallet'])).first()
        if product is None:
            continue

        if element.get('cell_destination') is not None:
            cell_destination = StorageCell.objects.filter(
                Q(external_key=element['cell_destination']) | Q(guid=element['cell_destination'])).first()
        else:
            cell_destination = None

        count = 0 if element.get('count') is None else element['count']
        operation_products = OperationCell.objects.create(cell_source=cell, count=count, product=product,
                                                          cell_destination=cell_destination)
        operation_products.fill_properties(operation)


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
        pass
        # cell_row = OperationCell.objects.filter(operation=instance.guid, product__guid=element.product,
        #                                         cell__guid=element.changed_cell).first()
        # if cell_row is None:
        #     continue
        #
        # cell_row.changed_cell = cell_row.cell
        # cell_row.cell = StorageCell.objects.filter(guid=element.cell).first()
        # cell_row.save()
    return instance.guid
