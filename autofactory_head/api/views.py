from django.db import transaction
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import viewsets, generics

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
    add_marks_to_marking_operation,
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
    DeviceSerializer
)

User = get_user_model()


class OrganizationList(generics.ListAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class UserRetrieve(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        instance = request.user
        serializer = UserSerializer(instance)
        return Response(serializer.data)


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class StorageList(generics.ListAPIView):
    queryset = Storage.objects.all()
    serializer_class = StorageSerializer


class DepartmentList(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class LineList(generics.ListAPIView):
    queryset = Line.objects.all()
    serializer_class = LineSerializer


class DeviceViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Device.objects.all()
        queryset = queryset.filter(mode=Device.AUTO_SCANNER)
        serializer = DeviceSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
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
        if request.user.device is None:
            raise APIException("У пользователя не определено устройство")

        request.user.device = None
        request.user.save()
        return Response({'detail': 'success'})


class MarkingViewSet(viewsets.ViewSet):
    def list(self, request):
        """Отправляет список невыгруженных маркировок по пользователю"""

        queryset = MarkingOperation.objects.all()
        queryset = queryset.filter(unloaded=False, author=request.user)
        serializer = MarkingSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Создает новую маркировку"""

        serializer = MarkingSerializer(data=request.data)
        if serializer.is_valid():
            author = request.user
            if MarkingOperation.objects.filter(author=author,
                                               closed=False).exists():
                raise APIException("Маркировка уже запущена")
            line = author.line if serializer.validated_data.get(
                'line') is None else serializer.validated_data.get('line')

            serializer.save(author=author, line=line)
            return Response(serializer.data)
        return Response(serializer.errors)

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
            add_marks_to_marking_operation(marking, data)
            register_to_exchange(marking)
            marking.close()
            if request.user.role == User.VISION_OPERATOR:
                clear_raw_marks(marking)

        return Response({'detail': 'success'})

    def confirm_unloading(self, request):
        """Подтверждение выгрузки маркировок во внешнюю систему"""
        return Response({'detail': 'success'})

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
#
# @api_view(['POST', ])
# def remove_marks(request):
#     serializer = ChangeMarkListSerializer(data=request.data)
#     if serializer.is_valid():
#         marks = unloaded_marks()
#         indexes_to_remove = []
#         for mark in serializer.validated_data.get('marks'):
#             if not marks.filter(mark=mark).exists():
#                 continue
#             for element in marks.filter(mark=mark):
#                 if indexes_to_remove.count(element.get('pk')):
#                     continue
#                 indexes_to_remove.append(element.get('pk'))
#         for index in indexes_to_remove:
#             MarkingOperationMarks.objects.get(pk=index).delete()
#
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors,
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @api_view(['POST', ])
# def add_marks(request):
#     serializer = ChangeMarkListSerializer(data=request.data)
#     if serializer.is_valid():
#         shift = ShiftOperation.objects.filter(
#             guid=serializer.validated_data.get('shift_guid')).get()
#         mark_filter = {'manual_editing': True, 'shift': shift}
#         if MarkingOperation.objects.filter(**mark_filter).exists():
#             marking = MarkingOperation.objects.filter(**mark_filter).get()
#         else:
#             marking = MarkingOperation.objects.create(**mark_filter)
#
#         fill_marks(marking, serializer.validated_data.get('marks'))
#
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors,
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#

#
# @api_view(['POST', ])
# @transaction.atomic
# def shift_close(request):
#     if not ShiftOperation.objects.filter(author=request.user,
#                                          closed=False).exists():
#         raise APIException("Нет открытых смен")
#
#     shift = ShiftOperation.objects.get(author=request.user, closed=False)
#     shift.closed = True
#     shift.save()
#
#     start_date = shift.date
#     end_date = datetime.datetime.now()
#
#     # marking
#     if RawMark.objects.filter(date__range=[start_date, end_date]).exists():
#         marking = MarkingOperation.objects.create(shift=shift,
#                                                   author=request.user)
#         fill_marks(marking, RawMark.objects.filter(
#             date__range=[start_date, end_date]).values())
#
#     # prepare to exchange
#     # TODO: нужно выбирать режим закрытия смены.
#     register_for_exchange()
#
#     return Response(status=status.HTTP_202_ACCEPTED)
#
