import base64

from django.conf import settings
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics
from rest_framework.exceptions import APIException
from rest_framework.response import Response

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
    create_marking_marks,
    remove_marks,
    get_marks_to_unload,
    confirm_marks_unloading,
    create_pallet,
    change_pallet_content
)
from packing.models import (
    MarkingOperation,
    RawMark,
    Pallet,
    Task
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
    MarksSerializer,
    ConfirmUnloadingSerializer,
    LogSerializer,
    PalletWriteSerializer,
    PalletReadSerializer, PalletUpdateSerializer,
    ChangePalletContentSerializer, TaskUpdateSerializer, TaskSerializer
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


class ProductViewSet(generics.ListCreateAPIView):
    """Список и создание товаров"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class StorageList(generics.ListAPIView):
    """Список складов"""
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer


class DepartmentList(generics.ListCreateAPIView):
    """Список и создание подразделений"""
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
    """Используется для создания маркировок и отображения списка маркировок"""
    serializer_class = MarkingSerializer
    queryset = MarkingOperation.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('line', 'closed', 'unloaded', 'guid')

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

        if serializer.validated_data.get('aggregations') is None:
            serializer.save(**values)
        else:
            data = serializer.validated_data.pop('aggregations')
            instance = serializer.save(**values)
            marking_close(instance, data)


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

        marking_close(marking, data)
        return Response({'detail': 'success'})


class MarksViewSet(viewsets.ViewSet):
    """Добавляет марки в существующую операцию маркировки"""

    def add_marks(self, request):
        serializer = MarksSerializer(data=request.data, source='post_request')
        if serializer.is_valid():
            operation = MarkingOperation.objects.get(
                guid=serializer.validated_data['marking'])
            create_marking_marks(operation,
                                 [{'mark': i} for i in
                                  serializer.validated_data['marks']])
            return Response(serializer.data)
        return Response(serializer.errors)

    def remove_marks(self, request):
        serializer = MarksSerializer(data=request.data)
        if serializer.is_valid():
            remove_marks(serializer.validated_data['marks'])
            return Response(serializer.data)
        return Response(serializer.errors)

    def marks_to_unload(self, request):
        return Response(data=get_marks_to_unload())

    def confirm_unloading(self, request):
        serializer = ConfirmUnloadingSerializer(data=request.data)
        if serializer.is_valid():
            confirm_marks_unloading(serializer.validated_data['operations'])
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


class PalletListViewSet(generics.ListCreateAPIView):
    """Используется для создания маркировок и отображения списка паллет"""
    serializer_class = PalletReadSerializer
    queryset = Pallet.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('id', 'guid',)

    def get_serializer(self, *args, **kwargs):
        if self.request.stream is None:
            return super().get_serializer(*args, **kwargs)
        else:
            return PalletWriteSerializer(data=self.request.data, many=True)

    def perform_create(self, serializer):
        create_pallet(serializer.validated_data)


class PalletUpdate(generics.UpdateAPIView):
    queryset = Pallet.objects.all()
    lookup_field = 'id'
    serializer_class = PalletUpdateSerializer


class PalletViewSet(viewsets.ViewSet):
    def change_content(self, request):
        serializer = ChangePalletContentSerializer(data=request.data)
        if serializer.is_valid():
            change_pallet_content(serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors)


class TaskUpdate(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer


class TaskListView(generics.ListAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('type_task', 'guid',)
