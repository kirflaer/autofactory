from django.db.models.signals import pre_delete
from .models import InventoryOperation, OperationCell, StorageCellContentState, StatusCellContent
from django.dispatch import receiver


@receiver(pre_delete, sender=InventoryOperation)
def pre_delete_inventory(sender, **kwargs):
    cells = OperationCell.objects.filter(operation=kwargs['instance'].guid)
    if not cells.exists():
        return

    for row in cells:
        states = StorageCellContentState.objects.filter(pallet=row.pallet, cell=row.cell_source,
                                                        status=StatusCellContent.PLACED)
        if states.exists():
            states.delete()
    cells.delete()
