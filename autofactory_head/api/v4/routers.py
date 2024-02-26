from api.v4.models import WriteOffTask, InventoryAddressWarehouseTask
from api.v4.serializers import (
    PalletCollectOperationWriteSerializer, ShipmentOperationReadSerializerV4,
    PalletCollectShipmentSerializerV4, WriteOffOperationReadSerializer, WriteOffOperationWriteSerializer,
    InventoryAddressWarehouseReadSerializer, InventoryAddressWarehouseWriteSerializer, CancelShipmentWriteSerializer,
    CancelShipmentReadSerializer, MovementShipmentWriteSerializer, MovementShipmentReadSerializer
)
from api.v4.services import (
    create_collect_operation, create_write_off_operation, change_content_write_off_operation,
    create_inventory_operation, change_content_inventory_operation, create_cancel_shipment,
    check_pallet_collect_shipment, create_movement_shipment, change_property_inventory,
    update_pallet_collect_operation,
)
from tasks.models import TaskBaseModel
from tasks.task_services import RouterTask
from warehouse_management.models import (
    PalletCollectOperation, ShipmentOperation, WriteOffOperation, InventoryAddressWarehouseOperation,
    CancelShipmentOperation, MovementShipmentOperation, SelectionOperation,
)
from warehouse_management.serializers import (
    PalletReadSerializer,
    PalletCollectOperationReadSerializer,
    ShipmentOperationWriteSerializer,
    SelectionOperationWriteSerializer,
    SelectionOperationReadSerializer,
)
from warehouse_management.warehouse_services import (
    create_shipment,
    create_shipment_semi_product_no_date,
    create_selection_semi_product_no_date,
)


def get_task_router() -> dict[str: RouterTask]:
    """ Возвращает роутер для потомков Task.
    В зависимости от переданного типа задания формируется класс и сериализаторы"""

    return {'PALLET_COLLECT': RouterTask(task=PalletCollectOperation,
                                         create_function=create_collect_operation,
                                         read_serializer=PalletCollectOperationReadSerializer,
                                         write_serializer=PalletCollectOperationWriteSerializer,
                                         content_model=TaskBaseModel,
                                         answer_serializer=PalletReadSerializer),
            'SHIPMENT': RouterTask(task=ShipmentOperation,
                                   create_function=create_shipment,
                                   read_serializer=ShipmentOperationReadSerializerV4,
                                   write_serializer=ShipmentOperationWriteSerializer,
                                   content_model=TaskBaseModel,
                                   custom_methods={'check_pallet_collect': check_pallet_collect_shipment}),
            'PALLET_COLLECT_SHIPMENT': RouterTask(task=PalletCollectOperation,
                                                  create_function=None,
                                                  read_serializer=PalletCollectShipmentSerializerV4,
                                                  write_serializer=None,
                                                  content_model=TaskBaseModel,
                                                  change_properties_function=update_pallet_collect_operation),
            'WRITE_OFF': RouterTask(task=WriteOffOperation,
                                    create_function=create_write_off_operation,
                                    read_serializer=WriteOffOperationReadSerializer,
                                    write_serializer=WriteOffOperationWriteSerializer,
                                    content_model=WriteOffTask,
                                    change_content_function=change_content_write_off_operation),
            'INVENTORY_ADDRESS_WAREHOUSE': RouterTask(task=InventoryAddressWarehouseOperation,
                                                      create_function=create_inventory_operation,
                                                      read_serializer=InventoryAddressWarehouseReadSerializer,
                                                      write_serializer=InventoryAddressWarehouseWriteSerializer,
                                                      content_model=InventoryAddressWarehouseTask,
                                                      change_content_function=change_content_inventory_operation,
                                                      change_properties_function=change_property_inventory),
            'CANCEL_SHIPMENT': RouterTask(task=CancelShipmentOperation,
                                          create_function=create_cancel_shipment,
                                          read_serializer=CancelShipmentReadSerializer,
                                          write_serializer=CancelShipmentWriteSerializer,
                                          content_model=TaskBaseModel),
            'MOVEMENT_WITH_SHIPMENT': RouterTask(task=MovementShipmentOperation,
                                                 create_function=create_movement_shipment,
                                                 read_serializer=MovementShipmentReadSerializer,
                                                 write_serializer=MovementShipmentWriteSerializer,
                                                 content_model=TaskBaseModel),
            'SHIPMENT_MOVEMENT': RouterTask(
                task=ShipmentOperation,
                create_function=create_shipment_semi_product_no_date,
                read_serializer=ShipmentOperationReadSerializerV4,
                write_serializer=ShipmentOperationWriteSerializer,
                content_model=TaskBaseModel,
                custom_methods={'check_pallet_collect': check_pallet_collect_shipment}
            ),
            'SELECTION_MOVEMENT': RouterTask(task=SelectionOperation,
                                             create_function=create_selection_semi_product_no_date,
                                             read_serializer=SelectionOperationReadSerializer,
                                             write_serializer=SelectionOperationWriteSerializer,
                                             content_model=TaskBaseModel),
            }
