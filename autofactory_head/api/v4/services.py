from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import APIException

from catalogs.models import Product
from tasks.models import TaskStatus
from warehouse_management.models import (
    PalletCollectOperation, WriteOffOperation, Pallet, OperationPallet, PalletSource, TypeCollect,
    InventoryAddressWarehouseOperation, InventoryAddressWarehouseContent, StorageCell, PalletStatus,
    CancelShipmentOperation, ShipmentOperation, MovementShipmentOperation
)
from warehouse_management.warehouse_services import (
    create_pallets, fill_operation_pallets, get_or_create_external_source, remove_boxes_from_pallet,
    fill_operation_cells
)

User = get_user_model()


@transaction.atomic
def create_collect_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения"""
    result = []
    operation = PalletCollectOperation.objects.create(status=TaskStatus.WORK, user=user)
    pallets = create_pallets(serializer_data['pallets'], user=user)
    fill_operation_pallets(operation, pallets)
    result += pallets
    return result


@transaction.atomic
def create_write_off_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию списания"""
    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        task = WriteOffOperation.objects.filter(external_source=external_source).first()
        if task is not None:
            result.append(task.guid)
            continue

        operation = WriteOffOperation.objects.create(external_source=external_source)

        for row in element['pallets']:
            pallet = Pallet.objects.filter(id=row['pallet']).first()
            OperationPallet.objects.create(operation=operation.guid, pallet=pallet, count=row['count'],
                                           type_operation='WRITE-OFF')
        result.append(operation.guid)
    return result


def prepare_pallet_collect_to_exchange(pallet: Pallet) -> None:
    operation_pallet_instance = OperationPallet.objects.filter(pallet=pallet).first()
    if not operation_pallet_instance:
        raise APIException('Не найдена операция сбора паллет')

    operation = PalletCollectOperation.objects.filter(guid=operation_pallet_instance.operation).first()
    if not operation:
        raise APIException('Не найдена операция сбора паллет')

    operation.status = TaskStatus.WAIT
    operation.save()


@transaction.atomic
def change_content_write_off_operation(content: dict[str: str], instance: WriteOffOperation) -> dict:
    """ Добавляет результат сбора операции списания"""
    if content.get('pallets') is not None:
        for element in content['pallets']:
            row = OperationPallet.objects.filter(guid=element.key).first()
            if not row:
                APIException('Не найдена паллета задания по ключу')

            PalletSource.objects.create(pallet_source=row.pallet, external_key=element.key,
                                        count=element.count, type_collect=TypeCollect.WRITE_OFF,
                                        related_task=instance.guid,
                                        product=row.pallet.product, weight=element.weight)
            remove_boxes_from_pallet(row.pallet, element.count, element.weight)
    if content.get('comment') is not None:
        instance.comment = content['comment']
        instance.save()

    return {'operation': instance.guid, 'result': 'success'}


@transaction.atomic
def create_inventory_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        task = InventoryAddressWarehouseOperation.objects.filter(external_source=external_source).first()
        if task is not None:
            result.append(task.guid)
            continue

        operation = InventoryAddressWarehouseOperation.objects.create(external_source=external_source)

        for row in element['products']:
            product = Product.objects.filter(external_key=row['product']).first()
            pallet = Pallet.objects.filter(id=row['pallet']).first()
            cell = StorageCell.objects.filter(external_key=row['cell']).first()
            inventory = InventoryAddressWarehouseContent.objects.create(
                product=product, pallet=pallet, cell=cell, plan=row['plan']
            )
            inventory.fill_properties(operation)

        result.append(operation.guid)
    return result


@transaction.atomic
def change_content_inventory_operation(content: dict[str: str], instance: InventoryAddressWarehouseOperation) -> dict:

    row = None
    if content.get('pallet'):
        element = content.get('pallet')
        row = InventoryAddressWarehouseContent.objects.create(
            pallet=Pallet.objects.get(external_key=element.key),
            cell=StorageCell.objects.get(external_key=element.cell),
            fact=element.count, priority=content.get('priority')
        )

        _create_pallet_source_to_inventory(
            row,
            ext_key=row.guid,
            related_task=instance.guid,
            count=element.count
        )

    if content.get('products'):

        for element in content['products']:
            row = InventoryAddressWarehouseContent.objects.filter(guid=element.key).first()

            if row is None:
                raise APIException('Не найдена строка в содержимом инвентаризации')

            _create_pallet_source_to_inventory(
                row,
                ext_key=element.key,
                related_task=instance.guid,
                count=element.count,
                weight=element.weight
            )

            row.fact += element.count
            row.save()

    return {'operation': instance.guid, 'result': 'success', 'row': row.guid if row else None}


@transaction.atomic
def divide_pallet(serializer_data: dict, user: User) -> list[Pallet]:
    current_pallet = Pallet.objects.get(id=serializer_data['source_pallet'])
    type_task = serializer_data.get('type_task', 'ACCEPTANCE_TO_STOCK')

    if current_pallet.product is not None:
        serializer_data['new_pallet']['product'] = current_pallet.product.guid

    if current_pallet.shift is not None:
        serializer_data['new_pallet']['shift'] = current_pallet.shift.guid

    if current_pallet.production_shop is not None:
        serializer_data['new_pallet']['production_shop'] = current_pallet.production_shop.guid

    instance = current_pallet.__dict__
    keys = ('batch_number', 'production_date', 'series')
    for key in keys:
        serializer_data['new_pallet'][key] = instance[key]

    operations_pallet = OperationPallet.objects.filter(
        pallet=current_pallet,
        type_operation=type_task.upper()
    )

    pallets = create_pallets((serializer_data['new_pallet'],))

    if len(pallets) and isinstance(pallets[0], Pallet):
        new_pallet = pallets[0]
    else:
        raise APIException('Ошибка при разделении паллет')

    match type_task.upper():
        case 'ACCEPTANCE_TO_STOCK':
            parent_task = None
            operation_pallet = operations_pallet.first()
            if operation_pallet:
                parent_task = operation_pallet.operation

            operation = PalletCollectOperation.objects.create(type_collect=TypeCollect.DIVIDED, user=user,
                                                              status=TaskStatus.WORK, parent_task=parent_task)
            fill_operation_pallets(operation, pallets)
        case 'MOVEMENT_WITH_SHIPMENT':
            operation_pallet = operations_pallet.filter(operation=serializer_data.get('task')).first()
            operation_pallet.dependent_pallet = new_pallet
            operation_pallet.save()
        case _:
            pass

    if current_pallet.weight != 0 and new_pallet.weight != 0:
        current_pallet.weight -= new_pallet.weight

    current_pallet.content_count -= new_pallet.content_count

    if current_pallet.content_count <= 0 or current_pallet.weight < 0:
        current_pallet.content_count = 0
        current_pallet.weight = 0
        current_pallet.status = PalletStatus.ARCHIVED

    current_pallet.save()

    return pallets


@transaction.atomic
def create_cancel_shipment(serializer_data, user: User) -> list:
    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        operation = CancelShipmentOperation.objects.filter(external_source=external_source)
        if operation:
            result.append(external_source.external_key)
            continue

        operation = CancelShipmentOperation.objects.create(external_source=external_source)
        fill_operation_cells(operation, element['pallets'])
        result.append(operation.guid)

        return result


def check_pallet_collect_shipment(instance: ShipmentOperation) -> dict:
    operations = PalletCollectOperation.objects.filter(parent_task=instance.guid)
    return {'all_task_count': operations.count(),
            'new_task_count': operations.filter(status=TaskStatus.NEW).count(),
            'close_task_count': operations.filter(status=TaskStatus.CLOSE).count(),
            'work_task_count': operations.filter(status=TaskStatus.WORK).count()}


@transaction.atomic
def create_movement_shipment(serializer_data, _: User) -> list:

    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        operation_movement = MovementShipmentOperation.objects.filter(external_source=external_source).first()
        if operation_movement:
            result.append(operation_movement.guid)
            return result

        operation_movement = MovementShipmentOperation.objects.create(external_source=external_source)
        result.append(operation_movement.guid)

        for pallet in element['pallets']:
            operation_pallet = OperationPallet.objects.create(
                pallet=Pallet.objects.get(id=pallet['pallet']),
                count=pallet['count'],
                external_source=external_source
            )
            operation_pallet.fill_properties(operation_movement)

        fill_operation_cells(operation_movement, element['pallets'])

    return result


def _create_pallet_source_to_inventory(
        content: InventoryAddressWarehouseContent,
        **kwargs
) -> PalletSource:

    return PalletSource.objects.create(
        pallet_source=content.pallet, external_key=kwargs.get('ext_key'),
        count=kwargs.get('count', 0), type_collect=TypeCollect.INVENTORY,
        related_task=kwargs.get('related_task'),
        product=content.product, weight=kwargs.get('weight', 0)
    )
