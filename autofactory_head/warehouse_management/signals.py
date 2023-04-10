from django.db.models.signals import pre_delete
from .models import InventoryOperation, OperationCell, StorageCellContentState, StatusCellContent, ShipmentOperation, \
    PalletCollectOperation, OperationPallet, SelectionOperation, WriteOffOperation
from django.dispatch import receiver


def remove_cell_and_state(operation_guid):
    cells = OperationCell.objects.filter(operation=operation_guid)
    if not cells.exists():
        return

    for row in cells:
        states = StorageCellContentState.objects.filter(pallet=row.pallet, cell=row.cell_source,
                                                        status=StatusCellContent.PLACED)
        if states.exists():
            states.delete()
    cells.delete()


@receiver(pre_delete, sender=InventoryOperation)
def pre_delete_inventory(sender, **kwargs):
    remove_cell_and_state(kwargs['instance'].guid)


@receiver(pre_delete, sender=SelectionOperation)
def pre_delete_inventory(sender, **kwargs):
    remove_cell_and_state(kwargs['instance'].guid)


@receiver(pre_delete, sender=ShipmentOperation)
def pre_delete_shipment(sender, **kwargs):
    instance = kwargs['instance']
    cells = OperationCell.objects.filter(operation=instance.guid)

    for cell in cells:
        cell.delete()

    pallet_collect = PalletCollectOperation.objects.filter(parent_task=instance.guid)
    for operation in pallet_collect:
        pallets = OperationPallet.objects.filter(operation=operation.guid)
        for row in pallets:
            row.pallet.delete()
        operation.delete()


@receiver(pre_delete, sender=WriteOffOperation)
def pre_delete_write_off(sender, **kwargs):
    OperationPallet.objects.filter(operation=kwargs['instance'].guid).delete()
