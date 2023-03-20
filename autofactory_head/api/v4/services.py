from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction

from tasks.models import TaskStatus
from warehouse_management.models import PalletCollectOperation
from warehouse_management.warehouse_services import create_pallets, fill_operation_pallets

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
