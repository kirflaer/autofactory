import base64
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from catalogs.models import (ActivationKey, Department, Device, Direction, Line, LineProduct, Organization, Product,
                             RegularExpression, Storage, TypeFactoryOperation, Unit)
from packing.marking_services import create_marking_marks, remove_marks
from packing.models import MarkingOperation, RawMark
from tasks.task_services import TaskException, get_content_queryset
from warehouse_management.models import Pallet, PalletStatus, StorageCell
from warehouse_management.serializers import PalletReadSerializer, PalletUpdateSerializer

from api.exceptions import ActivationFailed
from .serializers import (ConfirmUnloadingSerializer, DepartmentSerializer,
                          DeviceSerializer, DirectionSerializer, LineCreateSerializer, LogSerializer,
                          MarksSerializer, OrganizationSerializer, ProductSerializer,
                          RegularExpressionSerializer, StorageSerializer, TypeFactoryOperationSerializer,
                          UnitSerializer, UserSerializer, LineSerializer, StorageCellsSerializer, MarkingSerializer,
                          AggregationsSerializer)
from .services import confirm_marks_unloading

User = get_user_model()


class OrganizationList(generics.ListAPIView):
    """Список организаций"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class UserRetrieve(generics.RetrieveAPIView):
    """Данные пользователя"""
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        instance = request.user
        serializer = UserSerializer(instance)
        return Response(serializer.data)


class TypeFactoryOperationViewSet(generics.ListCreateAPIView):
    """ Типы производственных операций"""
    queryset = TypeFactoryOperation.objects.all()
    serializer_class = TypeFactoryOperationSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return TypeFactoryOperationSerializer(data=self.request.data,
                                                  many=True)


class ProductViewSet(generics.ListCreateAPIView):
    """Список и создание товаров"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.META['REQUEST_METHOD'] == 'GET':
            return super().get_serializer(*args, **kwargs)
        else:
            return ProductSerializer(data=self.request.data, many=True)


class StorageList(generics.ListAPIView):
    """Список складов"""
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer


class DepartmentList(generics.ListCreateAPIView):
    """Список и создание подразделений"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return DepartmentSerializer(data=self.request.data, many=True)


class DirectionListCreateView(generics.ListCreateAPIView):
    """Список и создание подразделений"""
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return DirectionSerializer(data=self.request.data, many=True)


class LineListCreateView(generics.ListCreateAPIView):
    """Список линий"""
    queryset = Line.objects.all()
    serializer_class = LineSerializer

    def perform_create(self, serializer):
        for element in serializer.validated_data:
            values = {'name': element.get('name')}

            managers = {'storage': Storage.objects,
                        'department': Department.objects,
                        'type_factory_operation': TypeFactoryOperation.objects}

            for key, value in managers.items():
                serializer_data = element.get(key)
                values[key] = value.filter(
                    external_key=serializer_data).first()

            line = Line.objects.create(**values)

            for key in element.get('products'):
                product = Product.objects.filter(external_key=key).first()
                if not LineProduct.objects.filter(product=product, line=line).exists():
                    LineProduct.objects.create(product=product, line=line)

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return LineCreateSerializer(data=self.request.data, many=True)


class DeviceViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def list_scanners(request):
        """Список автоматических сканеров"""
        queryset = Device.objects.all()
        queryset = queryset.filter(mode=Device.AUTO_SCANNER)
        serializer = DeviceSerializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    def create(request):
        """Создает устройство пользователя и связывает с пользователем
        Если устройство найдено по идентификатору то просто связывает"""
        if request.user.device is not None:
            raise APIException("У пользователя уже определено устройство")

        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data.get('identifier')
            number = None
            if not serializer.validated_data.get('activation_key') is None:
                number = serializer.validated_data.pop('activation_key')

            if Device.objects.filter(identifier=identifier).exists():
                instance = Device.objects.get(identifier=identifier)
            else:
                instance = serializer.save(mode=Device.DCT)

            if number is not None:
                activation_key = ActivationKey.objects.filter(number=number).first()
                if activation_key is None:
                    activation_key = ActivationKey.objects.create(number=number)

                if activation_key.device.count() and activation_key.device.first() != instance:
                    raise ActivationFailed('Код активирован на другом устройстве')
                instance.activation_key = activation_key
                instance.save()

            request.user.device = instance
            request.user.save()

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def remove(request):
        """Очищает связанное устройство у пользователя"""
        if request.user.device is None:
            raise APIException('У пользователя не определено устройство')

        request.user.device = None
        request.user.save()
        return Response({'detail': 'success'})


class MarkingListCreateViewSet(generics.ListCreateAPIView):
    """Используется для создания маркировок и отображения списка маркировок"""

    queryset = MarkingOperation.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('line', 'closed', 'unloaded', 'guid')

    def get_queryset(self):
        """ Добавляем нестандартные фильтры """
        queryset = self.queryset
        storage = self.request.query_params.get('storage')
        if storage is not None:
            queryset = queryset.filter(line__storage=storage)
        return queryset

    def marking_close(self, instance: MarkingOperation, validated_data: dict):
        pass

    def get_model_not_required_fields(self):
        return {'product': Product, 'organization': Organization}

    def get_marking_init_data(self, serializer: MarkingSerializer) -> dict:
        line = serializer.validated_data.get('line')
        line = self.request.user.line if line is None else line

        values = {'author': self.request.user,
                  'line': line}

        model_not_required_fields = self.get_model_not_required_fields()

        for key, value in model_not_required_fields.items():
            guid = serializer.validated_data.get(key)
            if guid is None:
                continue
            values[key] = value.objects.filter(pk=guid).first()
        return values


class MarksViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def confirm_unloading(request):
        """ Подтверждение об успешной выгрузке маркировки """
        serializer = ConfirmUnloadingSerializer(data=request.data)
        if serializer.is_valid():
            confirm_marks_unloading(serializer.validated_data['operations'])
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def add_marks(request):
        """Добавляет марки в существующую операцию маркировки"""
        serializer = MarksSerializer(data=request.data, source='post_request')
        if serializer.is_valid():
            operation = MarkingOperation.objects.get(
                guid=serializer.validated_data['marking'])
            create_marking_marks(operation,
                                 [{'mark': i} for i in
                                  serializer.validated_data['marks']])
            return Response({'detail': 'success'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def remove_marks(request):
        """ Удаляет марки из текущей маркировки """
        serializer = MarksSerializer(data=request.data)
        if serializer.is_valid():
            remove_marks(serializer.validated_data['marks'])
            return Response(serializer.data)
        return Response(serializer.errors)


class LogCreateViewSet(generics.CreateAPIView):
    serializer_class = LogSerializer

    def perform_create(self, serializer):
        data = serializer.validated_data.pop('data')
        serializer.save(server_version=settings.VERSION,
                        username=self.request.user.username,
                        device=self.request.user.device,
                        level=self.request.user.log_level,
                        data=base64.b64decode(data))


class RegExpList(generics.ListAPIView):
    """Список организаций"""
    queryset = RegularExpression.objects.all()
    serializer_class = RegularExpressionSerializer


class UnitsCreateListSet(generics.ListCreateAPIView):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

    def get_serializer(self, *args, **kwargs):
        return UnitSerializer(data=self.request.data, many=True)


class StorageCellsListCreateViewSet(generics.ListCreateAPIView):
    """Список и создание складских ячеек"""
    queryset = StorageCell.objects.all()
    serializer_class = StorageCellsSerializer

    def get_serializer(self, *args, **kwargs):
        if self.request.META['REQUEST_METHOD'] == 'GET':
            return super().get_serializer(*args, **kwargs)
        else:
            return StorageCellsSerializer(data=self.request.data, many=True)


class MarkingViewSet(viewsets.ViewSet):
    def close_marking(self, instance: MarkingOperation, validated_data: dict):
        pass

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

        self.close_marking(marking, data)
        return Response({'detail': 'success'})
