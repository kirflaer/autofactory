from django.db import transaction
from rest_framework import generics, status
from django.contrib.auth import get_user_model

from catalogs.models import Organization, Product
import datetime
import base64
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from .serializers import (
    OrganizationSerializer,
    ProductSerializer,
    ShiftSerializer,
    ShiftOpenSerializer,
    RawDeviceData
)
from factory_core.models import ShiftOperation
from marking.models import (
    DeviceSignal,
    RawMark,
    MarkingOperation,
    MarkingOperationMarks
)
from catalogs.models import Device

User = get_user_model()


@api_view(['POST', ])
def devices_marking(request):
    serializer = RawDeviceData(data=request.data)
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
    serializer = RawDeviceData(data=request.data)
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
    author = request.user
    if ShiftOperation.objects.filter(author=author, closed=False).exists():
        raise APIException("Смена уже открыта")

    serializer = ShiftOpenSerializer(data=request.data)
    if serializer.is_valid():
        date = serializer.validated_data.get('date')
        production_date = datetime.datetime.strptime(date, '%d.%m.%Y')
        author = request.user
        product = Product.objects.get(
            guid=serializer.validated_data.get('product'))
        serializer.save(production_date=production_date, author=author,
                        product=product)
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
    end_date = datetime.datetime.today()
    if RawMark.objects.filter(date__range=[start_date, end_date]).exists():
        marking = MarkingOperation.objects.create(shift=shift,
                                                  author=request.user)
        for value in RawMark.objects.values():
            mark = value['mark']
            sku = mark[2:15]
            product = None
            if Product.objects.filter(sku=sku).exists():
                product = Product.objects.get(sku=sku)

            mark_bytes = mark.encode("utf-8")
            base64_bytes = base64.b64encode(mark_bytes)
            base64_string = base64_bytes.decode("utf-8")
            MarkingOperationMarks.objects.create(operation=marking,
                                                 mark=mark,
                                                 encoded_mark=base64_string,
                                                 product=product)

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
