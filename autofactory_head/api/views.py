from django.db import transaction
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import viewsets, generics
from django_filters.rest_framework import DjangoFilterBackend
import time

from django.contrib.auth import get_user_model

from catalogs.models import (
    Organization,
    Product,
    Device,
    Line,
    Department,
    Storage
)

from packing.marking_services import (
    marking_close,
    add_marks,
    remove_marks,
    clear_raw_marks,
    register_to_exchange
)

from packing.models import (
    MarkingOperation,
    RawMark
)

from .serializers import (
    OrganizationSerializer,
    ProductSerializer,
    MarkingSerializer,
    UserSerializer,
    StorageSerializer,
    DepartmentSerializer,
    LineSerializer,
    AggregationsSerializer,
    DeviceSerializer,
    MarksSerializer
)

User = get_user_model()


class OrganizationList(generics.ListAPIView):
    """Список организаций"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class UserRetrieve(generics.RetrieveAPIView):
    """Данные пользователя"""

    def retrieve(self, request, *args, **kwargs):
        instance = request.user
        serializer = UserSerializer(instance)
        return Response(serializer.data)


class ProductList(generics.ListAPIView):
    """Список товаров"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class StorageList(generics.ListAPIView):
    """Список складов"""
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer


class DepartmentList(generics.ListAPIView):
    """Список подразделений"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class LineList(generics.ListAPIView):
    """Список линий"""
    queryset = Line.objects.all()
    serializer_class = LineSerializer


class DeviceViewSet(viewsets.ViewSet):
    def list_scanners(self, request):
        """Список автоматических сканеров"""
        queryset = Device.objects.all()
        queryset = queryset.filter(mode=Device.AUTO_SCANNER)
        serializer = DeviceSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Создает устройство пользователя и связывает с пользователем
        Если устройство найдено по идентификатору то просто связывает"""
        if not request.user.device is None:
            raise APIException("У пользователя уже определено устройство")

        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data.get('identifier')
            if Device.objects.filter(identifier=identifier).exists():
                instance = Device.objects.get(identifier=identifier)
            else:
                instance = serializer.save(mode=Device.DCT)

            request.user.device = instance
            request.user.save()

            return Response(serializer.data)
        return Response(serializer.errors)

    def remove(self, request):
        """Очищает связанное устройство у пользователя"""
        if request.user.device is None:
            raise APIException("У пользователя не определено устройство")

        request.user.device = None
        request.user.save()
        return Response({'detail': 'success'})


class MarkingListCreateViewSet(generics.ListCreateAPIView):
    serializer_class = MarkingSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('line',)

    def perform_create(self, serializer):
        line = serializer.validated_data.get('line')
        line = self.request.user.line if line is None else line

        values = {'author': self.request.user,
                  'line': line}

        product = serializer.validated_data.get('product')
        if not product is None:
            values['product'] = Product.objects.filter(pk=product).first()

        organization = serializer.validated_data.get('organization')
        if not organization is None:
            values['organization'] = Organization.objects.filter(
                pk=organization).first()

        serializer.save(**values)

    def get_queryset(self):
        queryset = MarkingOperation.objects.all()
        queryset = queryset.filter(closed=False)
        return queryset


class MarkingViewSet(viewsets.ViewSet):
    def close(self, request, pk=None):
        """Закрывает текущую маркировку
        Если закрытие происходит с ТСД отправляется набор марок
        Если закрытие от автоматического сканера марки берутся из RawMark"""

        marking = MarkingOperation.objects.filter(guid=pk)
        if not marking.exists():
            raise APIException("Маркировка не найдена")

        marking = MarkingOperation.objects.get(guid=pk)
        if marking.closed:
            raise APIException("Маркировка уже закрыта")

        if request.user.role == User.PACKER:
            serializer = AggregationsSerializer(data=request.data, many=True)
            if serializer.is_valid():
                data = serializer.data
            else:
                return Response(serializer.errors)
        elif request.user.role == User.VISION_OPERATOR:
            data = RawMark.objects.filter(operation=marking).values()
        else:
            data = []

        with transaction.atomic():
            marking_close(marking, data)
            # register_to_exchange(marking)
            # marking.close()
            # if request.user.role == User.VISION_OPERATOR:
            #     clear_raw_marks(marking)

        return Response({'detail': 'success'})


class MarksViewSet(viewsets.ViewSet):
    """Добавляет марки в существующую операцию маркировки"""

    def add_marks(self, request):
        serializer = MarksSerializer(data=request.data, source='post_request')
        if serializer.is_valid():
            operation = MarkingOperation.objects.get(
                guid=serializer.validated_data['marking'])
            add_marks(operation, serializer.validated_data['marks'])
            return Response(serializer.data)
        return Response(serializer.errors)

    def remove_marks(self, request):
        serializer = MarksSerializer(data=request.data)
        if serializer.is_valid():
            remove_marks(serializer.validated_data['marks'])
            return Response(serializer.data)
        return Response(serializer.errors)

    def unload_marks(self, request):
        pass

# @api_view(['GET', ])
# def unload_marks(request):
#     # TODO: добавить необходимую сериализацию
#     values = MarkingOperationMarks.objects.filter(
#         operation__shift__ready_to_unload=True,
#         operation__shift__closed=True,
#     ).values('encoded_mark',
#              'product__external_key',
#              'operation__shift__production_date',
#              'operation__shift__batch_number',
#              'operation__shift__guid',
#              'operation__shift__organization__external_key',
#              'operation__shift__line__storage__external_key',
#              'operation__shift__line__department__external_key'
#              )
#
#     data = []
#     for value in values:
#         element = {'shift': value['operation__shift__guid'],
#                    'encoded_mark': value['encoded_mark'],
#                    'product': value['product__external_key'],
#                    'production_date': value[
#                        'operation__shift__production_date'].strftime(
#                        "%d.%m.%Y"),
#                    'batch_number': value['operation__shift__batch_number'],
#                    'organization': value[
#                        'operation__shift__organization__external_key'],
#                    'storage': value[
#                        'operation__shift__line__storage__external_key'],
#                    'department': value[
#                        'operation__shift__line__department__external_key']
#                    }
#         data.append(element)
#
#     return Response(data=data, status=status.HTTP_200_OK)
#
