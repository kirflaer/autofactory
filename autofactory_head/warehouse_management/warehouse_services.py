from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction

from catalogs.models import ExternalSource, Product, Storage, StorageCell
from tasks.models import TaskStatus, TaskBaseModel
from tasks.task_services import RouterContent
from warehouse_management.models import (AcceptanceOperation, Pallet, OperationBaseOperation, OperationPallet,
                                         OperationProduct,
                                         PalletStatus, PalletCollectOperation, PlacementToCellsOperation, OperationCell,
                                         PlacementToCellsTask, MovementBetweenCellsOperation)
from warehouse_management.serializers import (
    AcceptanceOperationReadSerializer, AcceptanceOperationWriteSerializer, PalletCollectOperationWriteSerializer,
    PalletCollectOperationReadSerializer, PlacementToCellsOperationWriteSerializer,
    PlacementToCellsOperationReadSerializer, MovementBetweenCellsOperationWriteSerializer,
    MovementBetweenCellsOperationReadSerializer)

User = get_user_model()


def get_content_router() -> dict[str: RouterContent]:
    """ Возвращает роутер для потомков Task.
    В зависимости от переданного типа задания формируется класс и сериализаторы"""

    return {'ACCEPTANCE_TO_STOCK': RouterContent(task=AcceptanceOperation,
                                                 create_function=create_acceptance_operation,
                                                 read_serializer=AcceptanceOperationReadSerializer,
                                                 write_serializer=AcceptanceOperationWriteSerializer,
                                                 content_model=TaskBaseModel,
                                                 change_content_function=None),
            'PALLET_COLLECT': RouterContent(task=PalletCollectOperation,
                                            create_function=create_collect_operation,
                                            read_serializer=PalletCollectOperationReadSerializer,
                                            write_serializer=PalletCollectOperationWriteSerializer,
                                            content_model=TaskBaseModel,
                                            change_content_function=None),
            'PLACEMENT_TO_CELLS': RouterContent(task=PlacementToCellsOperation,
                                                create_function=create_placement_operation,
                                                read_serializer=PlacementToCellsOperationReadSerializer,
                                                write_serializer=PlacementToCellsOperationWriteSerializer,
                                                content_model=PlacementToCellsTask,
                                                change_content_function=change_content_placement_operation),
            'MOVEMENT_BETWEEN_CELLS': RouterContent(task=MovementBetweenCellsOperation,
                                                    create_function=create_movement_cell_operation,
                                                    read_serializer=MovementBetweenCellsOperationWriteSerializer,
                                                    write_serializer=MovementBetweenCellsOperationReadSerializer,
                                                    content_model=None,
                                                    change_content_function=None),
            }


@transaction.atomic
def create_movement_cell_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения между ячейками"""
    result = []
    for element in serializer_data:
        operation = MovementBetweenCellsOperation.objects.create()
        fill_operation_cells(operation, element['cells'])
        result.append(operation.guid)
    return result


@transaction.atomic
def create_placement_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию размещение в ячейках"""
    result = []
    for element in serializer_data:
        storage = Storage.objects.filter(external_key=element['storage']).first()
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
        operation = AcceptanceOperation.objects.create(external_source=external_source, storage=storage)
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


def fill_operation_pallets(operation: OperationBaseOperation, raw_data: Iterable[str]) -> None:
    """ Заполняет информацию о паллетах абстрактной операции """

    for pallet_id in raw_data:
        pallet = Pallet.objects.filter(id=pallet_id).first()
        if pallet is None:
            continue
        operation_pallets = OperationPallet.objects.create(pallet=pallet)
        operation_pallets.fill_properties(operation)


def fill_operation_cells(operation: OperationBaseOperation, raw_data: Iterable[dict[str: str]]) -> None:
    """ Заполняет ячейки абстрактной операции """

    for element in raw_data:
        cell = StorageCell.objects.filter(external_key=element['cell']).first()
        if cell is None:
            continue

        product = Product.objects.filter(external_key=element['product']).first()
        if product is None:
            continue

        if element.get('changed_cell') is not None:
            changed_cell = StorageCell.objects.filter(external_key=element['changed_cell']).first()
        else:
            changed_cell = None

        count = 0 if element.get('count') is None else element['count']
        operation_products = OperationCell.objects.create(cell=cell, count=count, product=product,
                                                          changed_cell=changed_cell)
        operation_products.fill_properties(operation)


def get_or_create_external_source(raw_data=dict[str: str]) -> ExternalSource:
    """ Создает либо находит элемент таблицы внешнего источника """

    external_source = ExternalSource.objects.filter(
        external_key=raw_data['external_source']['external_key']).first()
    if external_source is None:
        external_source = ExternalSource.objects.create(**raw_data['external_source'])
    return external_source


@transaction.atomic
def change_content_placement_operation(content: dict[str: str], instance: PlacementToCellsOperation) -> str:
    """ Изменяет содержимое операции размещение в ячейках"""
    for element in content['cells']:
        cell_row = OperationCell.objects.filter(operation=instance.guid, product__guid=element.product,
                                                cell__guid=element.changed_cell).first()
        if cell_row is None:
            continue

        cell_row.changed_cell = cell_row.cell
        cell_row.cell = StorageCell.objects.filter(guid=element.cell).first()
        cell_row.save()
    return instance.guid
