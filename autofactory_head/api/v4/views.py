from api.v2.views import TasksChangeViewSet
from api.v4.routers import get_task_router
from tasks.task_services import RouterTask


class TasksViewSet(TasksChangeViewSet):
    def get_routers(self) -> dict[str: RouterTask]:
        parent_routers = super().get_routers()
        return parent_routers | get_task_router()
