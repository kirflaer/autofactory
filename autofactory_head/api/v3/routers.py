from tasks.models import TaskBaseModel
from tasks.task_services import RouterTask
from warehouse_management.models import SelectionOperation, RepackingOperation, InventoryOperation
from warehouse_management.serializers import (SelectionOperationWriteSerializer, SelectionOperationReadSerializer,
                                              RepackingOperationReadSerializer, RepackingOperationWriteSerializer,
                                              InventoryWithPlacementOperationReadSerializer,
                                              InventoryWithPlacementOperationWriteSerializer)
from warehouse_management.warehouse_services import (create_selection_operation, create_repacking_operation,
                                                     create_inventory_with_placement_operation)


def get_task_router() -> dict[str: RouterTask]:
    """ Возвращает роутер для потомков Task.
    В зависимости от переданного типа задания формируется класс и сериализаторы"""

    return {'SELECTION': RouterTask(task=SelectionOperation,
                                    create_function=create_selection_operation,
                                    read_serializer=SelectionOperationReadSerializer,
                                    write_serializer=SelectionOperationWriteSerializer,
                                    content_model=TaskBaseModel,
                                    change_content_function=None),
            'REPACKING': RouterTask(task=RepackingOperation,
                                    create_function=create_repacking_operation,
                                    read_serializer=RepackingOperationReadSerializer,
                                    write_serializer=RepackingOperationWriteSerializer,
                                    content_model=TaskBaseModel,
                                    change_content_function=None),
            'INVENTORY_WITH_PLACEMENT': RouterTask(task=InventoryOperation,
                                                   create_function=create_inventory_with_placement_operation,
                                                   read_serializer=InventoryWithPlacementOperationReadSerializer,
                                                   write_serializer=InventoryWithPlacementOperationWriteSerializer,
                                                   content_model=TaskBaseModel,
                                                   change_content_function=None),
            }
