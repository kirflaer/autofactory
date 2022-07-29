from packing.models import MarkingOperation


def confirm_marks_unloading(operations: list) -> None:
    """Устанавливает признак unloaded у операций маркировок
    Подтверждая выгрузку во внешнюю систему"""
    for guid in operations:
        operation = MarkingOperation.objects.get(guid=guid)
        operation.unloaded = True
        operation.save()
