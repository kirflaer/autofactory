from api.v4.serializers import PalletCollectOperationWriteSerializer
from api.v4.services import create_collect_operation
from tasks.models import TaskBaseModel
from tasks.task_services import RouterTask
from warehouse_management.models import PalletCollectOperation
from warehouse_management.serializers import PalletReadSerializer, PalletCollectOperationReadSerializer


def get_task_router() -> dict[str: RouterTask]:
    """ Возвращает роутер для потомков Task.
    В зависимости от переданного типа задания формируется класс и сериализаторы"""

    return {'PALLET_COLLECT': RouterTask(task=PalletCollectOperation,
                                         create_function=create_collect_operation,
                                         read_serializer=PalletCollectOperationReadSerializer,
                                         write_serializer=PalletCollectOperationWriteSerializer,
                                         content_model=TaskBaseModel,
                                         answer_serializer=PalletReadSerializer),
            }
