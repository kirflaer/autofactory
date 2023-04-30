from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

from api.v3.views import TasksViewSet
from api.v4.routers import get_task_router
from api.v4.serializers import PalletUpdateSerializer, UsersListSerializer
from tasks.task_services import RouterTask
from warehouse_management.models import Pallet
from users.models import User


class TasksViewSetV4(TasksViewSet):
    def get_routers(self) -> dict[str: RouterTask]:
        parent_routers = super().get_routers()
        return parent_routers | get_task_router()


class PalletCollectUpdate(generics.UpdateAPIView):
    queryset = Pallet.objects.all()
    lookup_field = 'id'
    serializer_class = PalletUpdateSerializer


class UsersListViewSet(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)

    queryset = User.objects.filter(show_in_list=True)

    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('role',)

    serializer_class = UsersListSerializer
