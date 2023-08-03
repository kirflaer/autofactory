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
        pallet = Pallet.objects.filter(**kwargs).first()
        pallet_source = PalletSource.objects.filter(pallet_source=pallet)

        if not (pallet or pallet_source):
            raise APIException(f'Не найдена паллета в истории сбора')

        data = {
            'date': None,
            'client': 'Приход',
            'count': pallet.initial_count,
            'user': None,
            'pallet': pallet.name,
            'number': None
        }

        if pallet.creation_date:
            data['date'] = pallet.creation_date.strftime('%d.%m.%y-%H:%M')

        if pallet.collector:
            data['user'] = pallet.collector.username

        result = [data]

        for element in pallet_source:
            pallet_product = PalletProduct.objects.filter(external_key=element.external_key).first()
            if not pallet_product:
                continue
            data = {'date': None, 'client': None, 'count': element.count, 'user': None, 'pallet': None, 'number': None}

            if pallet.creation_date:
                data['date'] = pallet.creation_date.strftime('%d.%m.%y-%H:%M')

            if element.user:
                data['user'] = element.user.name

            if pallet_product.order:
                data['client'] = pallet_product.order.client_presentation
                if pallet_product.order.external_source:
                    data['number'] = re.findall(r'[1-9]+', pallet_product.order.external_source.number)[-1]

            if element.pallet:
                data['pallet'] = element.pallet.name

            result.append(data)

        return Response(result)

