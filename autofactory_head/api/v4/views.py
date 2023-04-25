from rest_framework import generics

from api.v3.views import TasksViewSet
from api.v4.routers import get_task_router
from api.v4.serializers import PalletUpdateSerializer
from tasks.task_services import RouterTask
from warehouse_management.models import Pallet


class TasksViewSetV4(TasksViewSet):
    def get_routers(self) -> dict[str: RouterTask]:
        parent_routers = super().get_routers()
        return parent_routers | get_task_router()


class PalletCollectUpdate(generics.UpdateAPIView):
    queryset = Pallet.objects.all()
    lookup_field = 'id'
    serializer_class = PalletUpdateSerializer
