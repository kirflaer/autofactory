import datetime
import re

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import APIException

from api.v3.views import TasksViewSet
from api.v4.routers import get_task_router
from api.v4.serializers import PalletUpdateSerializer, PalletDivideSerializer
from api.v4.services import divide_pallet
from tasks.task_services import RouterTask
from warehouse_management.models import Pallet, PalletSource, PalletProduct, OrderOperation
from warehouse_management.serializers import PalletReadSerializer

User = get_user_model()


class TasksViewSetV4(TasksViewSet):
    def get_routers(self) -> dict[str: RouterTask]:
        parent_routers = super().get_routers()
        return parent_routers | get_task_router()


class PalletCollectUpdate(generics.UpdateAPIView):
    queryset = Pallet.objects.all()
    lookup_field = 'id'
    serializer_class = PalletUpdateSerializer


class PalletDivideViewSet(viewsets.ViewSet):
    @staticmethod
    def divide_pallets(request: Request):
        serializer = PalletDivideSerializer(data=request.data)
        if serializer.is_valid():
            pallets = divide_pallet(serializer.validated_data, request.user)
            serializer = PalletReadSerializer(pallets[0])
            return Response({'status': 'success', 'new_pallet': serializer.data})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsersListViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def list(self, request: Request):
        self._validate_query_params(request)

        filter_fields = {'show_in_list': True}
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


class PalletCollectStorySerializer(generics.ListAPIView):

    def list(self, request, *args, **kwargs):
        pallet = Pallet.objects.get(**kwargs)
        pallet_source = PalletSource.objects.filter(pallet_source=pallet)

        if not (pallet or pallet_source):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        result = [{
            'date': pallet.creation_date.strftime('%d.%m.%y-%H:%M'),
            'client': 'Приход',
            'count': pallet.initial_count,
            'user': pallet.collector.username,
            'pallet': pallet.name,
            'number': None
        }]

        for element in pallet_source:
            pallet_product = PalletProduct.objects.filter(external_key=element.external_key).first()
            if not pallet_product:
                continue

            result.append({
                'date': element.pallet.creation_date.strftime('%d.%m.%y-%H:%M'),
                'client': pallet_product.order.client_presentation,
                'count': element.count,
                'user': element.pallet.collector.username,
                'pallet': element.pallet.name,
                'number': re.findall(r'[1-9]+', pallet_product.order.external_source.number)[-1]
            })

        return Response(result)

