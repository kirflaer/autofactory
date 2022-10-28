from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response

import api.views as api_views
import api.v3.serializers as api_serializers
from factory_core.models import Shift
from packing.marking_services import load_offline_marking_data, create_marking_marks
from packing.models import MarkingOperation


class ShiftListViewSet(generics.ListAPIView):
    """Список смен"""
    queryset = Shift.objects.all()
    serializer_class = api_serializers.ShiftSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('line', 'closed')


class ShiftUpdateView(generics.UpdateAPIView):
    queryset = Shift.objects.all()
    lookup_field = 'pk'
    serializer_class = api_serializers.ShiftSerializer


class MarkingOnLineViewSet(api_views.MarkingListCreateViewSet):
    serializer_class = api_serializers.MarkingSerializerOnline

    def get_model_not_required_fields(self):
        fields = super().get_model_not_required_fields()
        fields['shift'] = Shift
        return fields

    def perform_create(self, serializer):
        values = self.get_marking_init_data(serializer)
        serializer.save(**values)


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
    def close_marking(self, instance: MarkingOperation, validated_data: dict):
        with transaction.atomic():
            instance.closed = True
            instance.save()
            create_marking_marks(instance, validated_data)
