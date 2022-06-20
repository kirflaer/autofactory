from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction

from catalogs.models import ExternalSource, Product, Storage, StorageCell
from tasks.models import TaskStatus
from tasks.task_services import RouterContent
from warehouse_management.models import (AcceptanceOperation, Pallet, BaseOperation, OperationPallet, OperationProduct,
                                         PalletStatus, PalletCollectOperation, PlacementToCellsOperation, OperationCell)
from warehouse_management.serializers import (
    AcceptanceOperationReadSerializer, AcceptanceOperationWriteSerializer, PalletCollectOperationWriteSerializer,
    PalletCollectOperationReadSerializer, PlacementToCellsOperationWriteSerializer)

User = get_user_model()


def get_content_router() -> dict[str: RouterContent]:
    """ Возвращает роутер для потомков Task.
    В зависимости от переданного типа задания формируется класс и сериализаторы"""

    return {'ACCEPTANCE_TO_STOCK': RouterContent(task=AcceptanceOperation,
                                                 create_function=create_acceptance_operation,
                                                 read_serializer=AcceptanceOperationReadSerializer,
                                                 write_serializer=AcceptanceOperationWriteSerializer),
            'PALLET_COLLECT': RouterContent(task=PalletCollectOperation,
                                            create_function=create_collect_operation,
                                            read_serializer=PalletCollectOperationReadSerializer,
                                            write_serializer=PalletCollectOperationWriteSerializer),
            'PLACEMENT_TO_CELLS': RouterContent(task=PlacementToCellsOperation,
                                                create_function=create_placement_operation,
                                                read_serializer=PlacementToCellsOperationWriteSerializer,
                                                write_serializer=PlacementToCellsOperationWriteSerializer)
            }


@transaction.atomic
def create_placement_operation(serializer_data: Iterable[dict[str: str]]) -> Iterable[str]:
    """ Создает операцию размещение в ячейках"""
    result = []
    for element in serializer_data:
        storage = Storage.objects.filter(guid=element['storage']).first()
        operation = PlacementToCellsOperation.objects.create(storage=storage)
        fill_operation_cells(operation, element['cells'])
        result.append(operation.guid)
    return result


@transaction.atomic
def create_collect_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения"""
    result = []
    for element in serializer_data:
        operation = PalletCollectOperation.objects.create(ready_to_unload=True, closed=True, status=TaskStatus.CLOSE,
                                                          user=user)
        pallets = create_pallets(element['pallets'])
        fill_operation_pallets(operation, pallets)
        result.append(operation.guid)
    return result


@transaction.atomic
def create_acceptance_operation(serializer_data: Iterable[dict[str: str]]) -> Iterable[str]:
    """ Создает операцию перемещения. Возвращает идентификаторы внешнего источника """

    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        result.append(external_source.external_key)
        operation = AcceptanceOperation.objects.filter(external_source=external_source).first()
        if operation is not None:
            continue
        operation = AcceptanceOperation.objects.create(external_source=external_source)
        fill_operation_pallets(operation, element['pallets'])
        fill_operation_products(operation, element['products'])

    return result


@transaction.atomic
def create_pallets(serializer_data: Iterable[dict[str: str]]) -> Iterable[str]:
    """ Создает паллету и наполняет ее кодами агрегации"""
    result = []

    for element in serializer_data:
        product = Product.objects.filter(guid=element['product']).first()
        pallet = Pallet.objects.filter(id=element['id'], product=product).first()
        if not pallet:
            product = element['product']
            element['product'] = Product.objects.filter(guid=product).first()

            serializer_keys = set(element.keys())
            class_keys = set(dir(Pallet))
            fields = {key: element[key] for key in (class_keys & serializer_keys)}
            pallet = Pallet.objects.create(**fields, status=PalletStatus.CONFIRMED)

        result.append(pallet.id)
    return result


def fill_operation_products(operation: BaseOperation, raw_data: Iterable[dict[str: str]]) -> None:
    """ Заполняет товары абстрактной операции """

    for task_product in raw_data:
        product = Product.objects.filter(external_key=task_product['product']).first()
        if product is None:
            continue

        weight = 0 if task_product.get('weight') is None else task_product['weight']
        count = 0 if task_product.get('count') is None else task_product['count']
        operation_products = OperationProduct.objects.create(product=product, weight=weight, count=count)
        operation_products.fill_properties(operation)


def fill_operation_pallets(operation: BaseOperation, raw_data: Iterable[str]) -> None:
    """ Заполняет информацию о паллетах абстрактной операции """

    for pallet_id in raw_data:
        pallet = Pallet.objects.filter(id=pallet_id).first()
        if pallet is None:
            continue
        operation_pallets = OperationPallet.objects.create(pallet=pallet)
        operation_pallets.fill_properties(operation)


def fill_operation_cells(operation: BaseOperation, raw_data: Iterable[dict[str: str]]) -> None:
    """ Заполняет ячейки абстрактной операции """

    for element in raw_data:
        cell = StorageCell.objects.filter(external_key=element['cell']).first()
        if cell is None:
            continue

        product = Product.objects.filter(external_key=element['product']).first()
        if product is None:
            continue

        count = 0 if element.get('count') is None else element['count']
        operation_products = OperationCell.objects.create(cell=cell, count=count, product=product)
        operation_products.fill_properties(operation)


def get_or_create_external_source(raw_data=dict[str: str]) -> ExternalSource:
    """ Создает либо находит элемент таблицы внешнего источника """

    external_source = ExternalSource.objects.filter(
        external_key=raw_data['external_source']['external_key']).first()
    if external_source is None:
        external_source = ExternalSource.objects.create(**raw_data['external_source'])
    return external_source
