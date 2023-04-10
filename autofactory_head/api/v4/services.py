from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction

from catalogs.models import ExternalSource
from tasks.models import TaskStatus
from warehouse_management.models import PalletCollectOperation, WriteOffOperation, Pallet, OperationPallet
from warehouse_management.warehouse_services import create_pallets, fill_operation_pallets, \
    get_or_create_external_source

User = get_user_model()


@transaction.atomic
def create_collect_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения"""
    result = []
    operation = PalletCollectOperation.objects.create(closed=True, status=TaskStatus.CLOSE, user=user,
                                                      ready_to_unload=True)
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
