from django.db import transaction
from rest_framework import generics, status
from django.contrib.auth import get_user_model

from catalogs.models import Organization, Product
import datetime
import base64
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response
import pytz
from django.utils import timezone

from .serializers import (
    OrganizationSerializer,
    ProductSerializer,
    ShiftSerializer,
    ShiftOpenSerializer,
    RawDeviceDataSerializer,
    ChangeMarkListSerializer,
    UnloadMarkSerializer
)
from factory_core.models import ShiftOperation
from factory_core.utils import register_for_exchange
from marking.models import (
    DeviceSignal,
    RawMark,
    MarkingOperation,
    MarkingOperationMarks
)
from marking.utils import fill_marks, unloaded_marks
from catalogs.models import Device

User = get_user_model()


@api_view(['GET', ])
def unload_marks(request):
    # TODO: добавить необходимую сериализацию
    values = MarkingOperationMarks.objects.filter(
        operation__shift__ready_to_unload=True,
        operation__shift__closed=True,
    ).values('encoded_mark',
             'product__external_key',
             'operation__shift__production_date',
             'operation__shift__batch_number',
             'operation__shift__guid',
             'operation__shift__organization__external_key',
             'operation__shift__line__storage__external_key',
             'operation__shift__line__department__external_key'
             )

    data = []
    for value in values:
        element = {'shift': value['operation__shift__guid'],
                   'encoded_mark': value['encoded_mark'],
                   'product': value['product__external_key'],
                   'production_date': value[
                       'operation__shift__production_date'].strftime(
                       "%d.%m.%Y"),
                   'batch_number': value['operation__shift__batch_number'],
                   'organization': value[
                       'operation__shift__organization__external_key'],
                   'storage': value[
                       'operation__shift__line__storage__external_key'],
                   'department': value[
                       'operation__shift__line__department__external_key']
                   }
        data.append(element)

    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['POST', ])
def remove_marks(request):
    serializer = ChangeMarkListSerializer(data=request.data)
    if serializer.is_valid():
        marks = unloaded_marks()
        indexes_to_remove = []
        for mark in serializer.validated_data.get('marks'):
            if not marks.filter(mark=mark).exists():
                continue
            for element in marks.filter(mark=mark):
                if indexes_to_remove.count(element.get('pk')):
                    continue
                indexes_to_remove.append(element.get('pk'))
        for index in indexes_to_remove:
            MarkingOperationMarks.objects.get(pk=index).delete()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', ])
def add_marks(request):
    serializer = ChangeMarkListSerializer(data=request.data)
    if serializer.is_valid():
        shift = ShiftOperation.objects.filter(
            guid=serializer.validated_data.get('shift_guid')).get()
        mark_filter = {'manual_editing': True, 'shift': shift}
        if MarkingOperation.objects.filter(**mark_filter).exists():
            marking = MarkingOperation.objects.filter(**mark_filter).get()
        else:
            marking = MarkingOperation.objects.create(**mark_filter)

        fill_marks(marking, serializer.validated_data.get('marks'))

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', ])
def devices_marking(request):
    serializer = RawDeviceDataSerializer(data=request.data)
    if serializer.is_valid():
        external_key = serializer.validated_data.get('device')
        device = Device.objects.get(external_key=external_key)
        for mark in serializer.validated_data.get('marks'):
            RawMark.objects.create(device=device, mark=mark)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', ])
def devices_status(request):
    serializer = RawDeviceDataSerializer(data=request.data)
    if serializer.is_valid():
        external_key = serializer.validated_data.get('device')
        device = Device.objects.get(external_key=external_key)
        DeviceSignal.objects.create(device=device)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', ])
@transaction.atomic
def shift_open(request):
    serializer = ShiftOpenSerializer(data=request.data)
    if serializer.is_valid():
        author = request.user
        if ShiftOperation.objects.filter(author=author, closed=False).exists():
            raise APIException("Смена уже открыта")

        device = author.line.device
        if not DeviceSignal.objects.filter(device=device).exists():
            raise APIException("Устройство недоступно")

        signal_time = DeviceSignal.objects.filter(device=device).values()[:1]
        signal_time = signal_time[0]['date']
        now = datetime.datetime.now(timezone.utc)

        if (now - signal_time).seconds > device.polling_interval:
            raise APIException("Устройство недоступно")

        date = serializer.validated_data.get('date')
        production_date = datetime.datetime.strptime(date, '%d.%m.%Y')
        author = request.user
        product = Product.objects.get(
            guid=serializer.validated_data.get('product'))
        serializer.save(production_date=production_date, author=author,
                        product=product, line=author.line)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', ])
@transaction.atomic
def shift_close(request):
    if not ShiftOperation.objects.filter(author=request.user,
                                         closed=False).exists():
        raise APIException("Нет открытых смен")

    shift = ShiftOperation.objects.get(author=request.user, closed=False)
    shift.closed = True
    shift.save()

    start_date = shift.date
    end_date = datetime.datetime.now()

    # marking
    if RawMark.objects.filter(date__range=[start_date, end_date]).exists():
        marking = MarkingOperation.objects.create(shift=shift,
                                                  author=request.user)
        fill_marks(marking, RawMark.objects.filter(
            date__range=[start_date, end_date]).values())

    # prepare to exchange
    # TODO: нужно выбирать режим закрытия смены.
    register_for_exchange()

    return Response(status=status.HTTP_202_ACCEPTED)


class ShiftList(generics.ListAPIView):
    serializer_class = ShiftSerializer

    def get_queryset(self):
        queryset = ShiftOperation.objects.all()
        queryset = queryset.filter(unloaded=False)
        return queryset


class OrganizationList(generics.ListAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
