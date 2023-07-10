import uuid
from django.contrib.auth import get_user_model

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import APIException

from rest_framework.response import Response
import api.views as api_views
import api.v3.serializers as api_serializers
from api.v2.views import TasksChangeViewSet
from api.v3.routers import get_task_router

from api.v3.services import load_manual_marks, load_offline_marking_data
from factory_core.models import Shift
from packing.marking_services import create_marking_marks, clear_raw_marks

from packing.models import MarkingOperation
from packing.marking_services import shift_close
from tasks.task_services import RouterTask
from warehouse_management.models import StorageArea, Pallet, StorageCell
from warehouse_management.serializers import (
    ChangeCellSerializer, PalletUpdateShipmentSerializer, PalletUpdateRepackingSerializer
)
from warehouse_management.warehouse_services import change_cell_content_state

User = get_user_model()


class ShiftListViewSet(generics.ListCreateAPIView):
    """Список смен"""
    queryset = Shift.objects.all()
    serializer_class = api_serializers.ShiftSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('line', 'closed', 'type')


class ShiftUpdateView(generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = Shift.objects.all()
    lookup_field = 'pk'
    serializer_class = api_serializers.ShiftUpdateSerializer

    def get_serializer_class(self):
        if self.request.stream is None:
            return api_serializers.ShiftRetrieveSerializer
        else:
            return api_serializers.ShiftUpdateSerializer


class MarkingOnLineViewSet(api_views.MarkingListCreateViewSet):
    serializer_class = api_serializers.MarkingSerializerOnlineRead

    def get_model_not_required_fields(self):
        fields = super().get_model_not_required_fields()
        fields['shift'] = Shift
        return fields

    def perform_create(self, serializer):
        values = self.get_marking_init_data(serializer)
        serializer.save(**values)

    def get_serializer_class(self):
        if self.request.stream is None:
            return api_serializers.MarkingSerializerOnlineRead
        else:
            return api_serializers.MarkingSerializerOnlineWrite


class MarkingOffLineViewSet(api_views.MarkingListCreateViewSet):
    serializer_class = api_serializers.MarkingSerializerOffline

    def create(self, request, *args, **kwargs):
        serializer = api_serializers.MarkingSerializerOffline(data=request.data)

        if serializer.is_valid():
            values = self.get_marking_init_data(serializer)
            marks = serializer.validated_data.pop('aggregations')
            instance = serializer.save(**values)
            load_offline_marking_data(instance, marks)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MarkingViewSet(api_views.MarkingViewSet):
    def close_marking(self, instance: MarkingOperation, validated_data: dict | list):
        with transaction.atomic():
            instance.closed = True
            instance.group = instance.shift.guid
            instance.save()

            if self.request.user.role == User.VISION_OPERATOR:
                create_marking_marks(instance, validated_data)
                clear_raw_marks(instance)
            else:
                load_manual_marks(instance, validated_data)


class TasksViewSet(TasksChangeViewSet):
    def get_routers(self) -> dict[str: RouterTask]:
        parent_routers = super().get_routers()
        return parent_routers | get_task_router()


class StorageAreaListCreateViewSet(generics.ListCreateAPIView):
    """Список и создание складских ячеек"""
    queryset = StorageArea.objects.all()
    serializer_class = api_serializers.StorageAreaSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.META['REQUEST_METHOD'] == 'GET':
            return super().get_serializer(*args, **kwargs)
        else:
            return api_serializers.StorageAreaSerializer(data=self.request.data, many=True)


class PalletViewSet(viewsets.ViewSet):
    @staticmethod
    def change_cell(request, pallet_id):
        try:
            guid = uuid.UUID(pallet_id)
            filter_kwargs = {'guid': guid}
        except ValueError:
            filter_kwargs = {'id': pallet_id}
        pallet = Pallet.objects.filter(**filter_kwargs).first()

        if not pallet:
            raise APIException('Паллета не найдена')

        serializer = ChangeCellSerializer(data=request.data)
        if serializer.is_valid():
            new_status = change_cell_content_state(serializer.validated_data, pallet)
            return Response({'status': new_status})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PalletShipmentUpdate(generics.UpdateAPIView):
    queryset = Pallet.objects.all()
    lookup_field = 'guid'
    serializer_class = PalletUpdateShipmentSerializer


class PalletRepackingUpdate(generics.UpdateAPIView):
    queryset = Pallet.objects.all()
    lookup_field = 'guid'
    serializer_class = PalletUpdateRepackingSerializer

    def perform_update(self, serializer):
        serializer.request_user = self.request.user
        serializer.save()


class CellRetrieveView(generics.RetrieveUpdateAPIView):
    queryset = StorageCell.objects.all()
    lookup_field = 'external_key'
    serializer_class = api_serializers.StorageCellsRetrieveSerializer
