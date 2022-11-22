from tasks.models import TaskBaseModel
from tasks.task_services import RouterTask
from warehouse_management.models import SelectionOperation
from warehouse_management.serializers import SelectionOperationWriteSerializer, SelectionOperationReadSerializer
from warehouse_management.warehouse_services import create_selection_operation


def get_task_router() -> dict[str: RouterTask]:
    """ Возвращает роутер для потомков Task.
    В зависимости от переданного типа задания формируется класс и сериализаторы"""

    return {'SELECTION': RouterTask(task=SelectionOperation,
                                    create_function=create_selection_operation,
                                    read_serializer=SelectionOperationReadSerializer,
                                    write_serializer=SelectionOperationWriteSerializer,
                                    content_model=TaskBaseModel,
                                    change_content_function=None)
            }
