from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import APIException

from catalogs.models import Product
from tasks.models import TaskStatus
from warehouse_management.models import (
    PalletCollectOperation, WriteOffOperation, Pallet, OperationPallet, PalletSource, TypeCollect,
    InventoryAddressWarehouseOperation, InventoryAddressWarehouseContent, StorageCell
)
from warehouse_management.warehouse_services import create_pallets, fill_operation_pallets, \
    get_or_create_external_source

User = get_user_model()


@transaction.atomic
def create_collect_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения"""
    result = []
    operation = PalletCollectOperation.objects.create(status=TaskStatus.WORK, user=user)
    pallets = create_pallets(serializer_data['pallets'])
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

    operation.status = TaskStatus.CLOSE
    operation.close()


@transaction.atomic
def change_content_write_off_operation(content: dict[str: str], instance: WriteOffOperation) -> dict:
    """ Добавляет результат сбора операции списания"""
    for element in content["pallets"]:
        row = OperationPallet.objects.filter(guid=element.key).first()
        if not row:
            APIException('Не найдена паллета задания по ключу')

        PalletSource.objects.create(pallet_source=row.pallet, external_key=element.key,
                                    count=element.count, type_collect=TypeCollect.WRITE_OFF, related_task=instance.guid,
                                    product=row.pallet.product, weight=element.weight)

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
            product = Product.objects.filter(guid=row['product']).first()
            pallet = Pallet.objects.filter(id=row['pallet']).first()
            cell = StorageCell.objects.filter(guid=row['cell']).first()
            inventory = InventoryAddressWarehouseContent.objects.create(
                product=product, pallet=pallet, cell=cell, plan=row['plan']
            )
            inventory.fill_properties(operation)

        result.append(operation.guid)
    return result


@transaction.atomic
def change_content_inventory_operation(content: dict[str: str], instance: InventoryAddressWarehouseOperation) -> dict:

    for element in content['products']:
        inventory_row = InventoryAddressWarehouseContent.objects.filter(
            operation=instance.guid,
            product__guid=element.product,
            plan=element.plan
        ).first()

        if inventory_row is None:
            continue

        inventory_row.fact = element.fact
        inventory_row.save()

    return {'operation': instance.guid, 'result': 'success'}
