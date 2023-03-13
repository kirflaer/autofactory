from api.v2.views import TasksChangeViewSet


class TasksViewSet(TasksChangeViewSet):
    def get_routers(self) -> dict[str: RouterTask]:
        parent_routers = super().get_routers()
        return parent_routers | get_task_router()