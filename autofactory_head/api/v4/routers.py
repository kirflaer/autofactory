from api.v4.models import WriteOffTask
from api.v4.serializers import PalletCollectOperationWriteSerializer, ShipmentOperationReadSerializerV4, \
    PalletCollectShipmentSerializerV4, WriteOffOperationReadSerializer, WriteOffOperationWriteSerializer
from api.v4.services import create_collect_operation, create_write_off_operation, change_content_write_off_operation
from tasks.models import TaskBaseModel
from tasks.task_services import RouterTask
from warehouse_management.models import PalletCollectOperation, ShipmentOperation, WriteOffOperation
from warehouse_management.serializers import (PalletReadSerializer, PalletCollectOperationReadSerializer,
                                              ShipmentOperationWriteSerializer, )
from warehouse_management.warehouse_services import create_shipment_operation


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
                                   create_function=create_shipment_operation,
                                   read_serializer=ShipmentOperationReadSerializerV4,
                                   write_serializer=ShipmentOperationWriteSerializer,
                                   content_model=TaskBaseModel,
                                   change_content_function=None),
            'PALLET_COLLECT_SHIPMENT': RouterTask(task=PalletCollectOperation,
                                                  create_function=None,
                                                  read_serializer=PalletCollectShipmentSerializerV4,
                                                  write_serializer=None,
                                                  content_model=TaskBaseModel,
                                                  change_content_function=None),
            'WRITE_OFF': RouterTask(task=WriteOffOperation,
                                    create_function=create_write_off_operation,
                                    read_serializer=WriteOffOperationReadSerializer,
                                    write_serializer=WriteOffOperationWriteSerializer,
                                    content_model=WriteOffTask,
                                    change_content_function=change_content_write_off_operation),
            }
