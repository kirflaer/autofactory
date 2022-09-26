from tasks.task_services import RouterTask, RouterContent
from tasks.models import TaskBaseModel

from warehouse_management.serializers import (AcceptanceOperationReadSerializer,
                                              AcceptanceOperationWriteSerializer,
                                              PalletCollectOperationWriteSerializer,
                                              PalletCollectOperationReadSerializer,
                                              PlacementToCellsOperationWriteSerializer,
                                              PlacementToCellsOperationReadSerializer,
                                              MovementBetweenCellsOperationWriteSerializer,
                                              MovementBetweenCellsOperationReadSerializer,
                                              ShipmentOperationReadSerializer,
                                              ShipmentOperationWriteSerializer,
                                              PalletReadSerializer,
                                              PalletCollectShipmentSerializer, OrderReadSerializer)

from warehouse_management.models import (AcceptanceOperation,
                                         PalletCollectOperation,
                                         PlacementToCellsOperation,
                                         MovementBetweenCellsOperation, ShipmentOperation, OrderOperation,
                                         PlacementToCellsTask, OperationPallet, Pallet)
from warehouse_management.warehouse_services import (create_acceptance_operation,
                                                     create_collect_operation,
                                                     create_placement_operation,
                                                     change_content_placement_operation,
                                                     create_movement_cell_operation,
                                                     create_shipment_operation, create_order_operation)


def get_task_router() -> dict[str: RouterTask]:
    """ Возвращает роутер для потомков Task.
    В зависимости от переданного типа задания формируется класс и сериализаторы"""

    return {'ACCEPTANCE_TO_STOCK': RouterTask(task=AcceptanceOperation,
                                              create_function=create_acceptance_operation,
                                              read_serializer=AcceptanceOperationReadSerializer,
                                              write_serializer=AcceptanceOperationWriteSerializer,
                                              content_model=TaskBaseModel,
                                              change_content_function=None),
            'PALLET_COLLECT': RouterTask(task=PalletCollectOperation,
                                         create_function=create_collect_operation,
                                         read_serializer=PalletCollectOperationReadSerializer,
                                         write_serializer=PalletCollectOperationWriteSerializer,
                                         content_model=TaskBaseModel,
                                         change_content_function=None),
            'PLACEMENT_TO_CELLS': RouterTask(task=PlacementToCellsOperation,
                                             create_function=create_placement_operation,
                                             read_serializer=PlacementToCellsOperationReadSerializer,
                                             write_serializer=PlacementToCellsOperationWriteSerializer,
                                             content_model=PlacementToCellsTask,
                                             change_content_function=change_content_placement_operation),
            'MOVEMENT_BETWEEN_CELLS': RouterTask(task=MovementBetweenCellsOperation,
                                                 create_function=create_movement_cell_operation,
                                                 read_serializer=MovementBetweenCellsOperationReadSerializer,
                                                 write_serializer=MovementBetweenCellsOperationWriteSerializer,
                                                 content_model=None,
                                                 change_content_function=None),
            'SHIPMENT': RouterTask(task=ShipmentOperation,
                                   create_function=create_shipment_operation,
                                   read_serializer=ShipmentOperationReadSerializer,
                                   write_serializer=ShipmentOperationWriteSerializer,
                                   content_model=TaskBaseModel,
                                   change_content_function=None),
            'ORDER': RouterTask(task=OrderOperation,
                                create_function=None,
                                read_serializer=OrderReadSerializer,
                                write_serializer=None,
                                content_model=None,
                                change_content_function=None),

            'PALLET_COLLECT_SHIPMENT': RouterTask(task=PalletCollectOperation,
                                                  create_function=None,
                                                  read_serializer=PalletCollectShipmentSerializer,
                                                  write_serializer=None,
                                                  content_model=TaskBaseModel,
                                                  change_content_function=None),
            }


def get_content_router() -> dict[str: RouterContent]:
    return {
        'PALLETS': RouterContent(
            object_model=Pallet,
            content_model=OperationPallet,
            serializer=PalletReadSerializer,
            object_key_name='pallet'
        )
    }
