from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import APIException

from api.v3.views import TasksViewSet
from api.v4.routers import get_task_router
from api.v4.serializers import PalletUpdateSerializer
from tasks.task_services import RouterTask
from warehouse_management.models import Pallet


User = get_user_model()


class TasksViewSetV4(TasksViewSet):
    def get_routers(self) -> dict[str: RouterTask]:
        parent_routers = super().get_routers()
        return parent_routers | get_task_router()


class PalletCollectUpdate(generics.UpdateAPIView):
    queryset = Pallet.objects.all()
    lookup_field = 'id'
    serializer_class = PalletUpdateSerializer


class UsersListViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def list(self, request: Request):
        self._validate_query_params(request)

        filter_fields = {'show_in_list':  True}
        filter_fields.update(request.query_params.dict())

        queryset = User.objects.filter(**filter_fields).values_list('username', flat=True)
        if len(queryset):
            return Response({'users': queryset})
        return Response({'users': []})

    @staticmethod
    def _validate_query_params(request: Request):
        model_fields = set(dir(User))
        query_keys = set(request.query_params.dict().keys())
        if len(query_keys.difference(model_fields)):
            raise APIException('Неверные параметры запроса')
