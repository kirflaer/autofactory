from django.http import JsonResponse
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException

from api.v1.serializers import (
    PalletCollectShipmentSerializer, ShipmentOperationReadSerializer, PalletShipmentSerializer
)
from api.v3.serializers import ShiftSerializer
from api.v4.services import prepare_pallet_collect_to_exchange
from catalogs.serializers import ExternalSerializer
from factory_core.models import Shift
from datetime import datetime as dt
from warehouse_management.models import (
    ShipmentOperation, PalletCollectOperation, OperationPallet, Pallet, PalletStatus, PalletProduct,
    SuitablePallets, WriteOffOperation, PalletSource, TypeCollect, InventoryAddressWarehouseOperation,
    InventoryAddressWarehouseContent, CancelShipmentOperation, OperationCell, StorageCell, MovementShipmentOperation
)
from warehouse_management.serializers import (
    PalletWriteSerializer, PalletProductSerializer, SuitablePalletSerializer, OperationPalletSerializer,
    PalletSourceReadSerializer, PalletReadSerializer, InventoryAddressWarehouseSerializer,
    InventoryWriteSerializer, StorageCellsSerializer
)
from catalogs.models import Line


class PalletCollectOperationWriteSerializer(serializers.Serializer):
    pallets = PalletWriteSerializer(many=True)
    shift = serializers.UUIDField()

    def validate(self, attrs):
        shift = Shift.objects.filter(guid=attrs.get('shift')).first()
        if not shift:
            raise APIException('Не найдена смена')

        if shift.closed:
            raise APIException('Смена закрыта')

        return super().validate(attrs)


class ShipmentOperationReadSerializerV4(ShipmentOperationReadSerializer):
    class Meta:
        model = ShipmentOperation
        fields = ('direction', 'date', 'number', 'guid', 'external_key', 'has_selection', 'manager', 'car_carrier')


class PalletProductReadSerializer(PalletProductSerializer):
    suitable_pallets = serializers.SerializerMethodField()

    @staticmethod
    def get_suitable_pallets(obj):
        pallets = SuitablePallets.objects.filter(pallet_product=obj)
        if not pallets.count():
            return []

        serializer = SuitablePalletSerializer(pallets, many=True)
        return serializer.data


class PalletShipmentSerializerV4(PalletShipmentSerializer):
    products = serializers.SerializerMethodField()

    @staticmethod
    def get_products(obj):
        products = PalletProduct.objects.filter(pallet=obj)
        serializer = PalletProductReadSerializer(products, many=True)
        return serializer.data


class PalletCollectShipmentSerializerV4(PalletCollectShipmentSerializer):
    pallets = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(read_only=True, slug_field='username')
    modified = serializers.DateTimeField(format='%H:%M')

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'date', 'number', 'status', 'pallets', 'user', 'is_owner', 'modified')

    @staticmethod
    def get_pallets(obj):
        pallet_guids = OperationPallet.objects.filter(operation=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallet_guids, status=PalletStatus.WAITED)
        serializer = PalletShipmentSerializerV4(pallets, many=True)
        return serializer.data


class WriteOffOperationWriteSerializer(serializers.Serializer):
    external_source = ExternalSerializer()
    pallets = OperationPalletSerializer(many=True)


class WriteOffOperationReadSerializer(serializers.ModelSerializer):
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')
    pallets = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = WriteOffOperation
        fields = ('guid', 'date', 'number', 'status', 'pallets', 'sources', 'external_key', 'comment')

    @staticmethod
    def get_sources(obj):
        keys = OperationPallet.objects.filter(operation=obj.guid).values_list('guid', flat=True)
        sources = PalletSource.objects.filter(external_key__in=list(keys), type_collect=TypeCollect.WRITE_OFF)
        serializer = PalletSourceReadSerializer(sources, many=True)
        return serializer.data

    @staticmethod
    def get_pallets(obj):
        pallets = OperationPallet.objects.filter(operation=obj.guid)
        result = []
        for row in pallets:
            serializer = PalletReadSerializer(row.pallet)
            result.append({'count': row.count,
                           'pallet': serializer.data,
                           'key': row.guid})
        return result

    @staticmethod
    def get_date(obj):
        if obj.external_source is None:
            return obj.date.strftime('%d.%m.%Y')

        try:
            date = dt.strptime(obj.external_source.date, '%Y-%m-%dT%H:%M:%S')
            date = date.strftime('%d.%m.%Y')
        except ValueError:
            date = obj.date.strftime('%d.%m.%Y')
        return date


class PalletUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('status',)
        model = Pallet

    def update(self, instance, validated_data):
        with transaction.atomic():
            prepare_pallet_collect_to_exchange(instance)
        return super().update(instance, validated_data)


class InventoryAddressWarehouseReadSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    external_source = ExternalSerializer()

    class Meta:
        model = InventoryAddressWarehouseOperation
        fields = (
            'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded',
            'products', 'sources'
        )

    @staticmethod
    def get_sources(obj):
        keys = InventoryAddressWarehouseContent.objects.filter(operation=obj.guid).values_list('guid', flat=True)
        sources = PalletSource.objects.filter(external_key__in=list(keys), type_collect=TypeCollect.INVENTORY)
        serializer = PalletSourceReadSerializer(sources, many=True)
        return serializer.data

    @staticmethod
    def get_products(obj):
        products = InventoryAddressWarehouseContent.objects.filter(operation=obj.guid)
        result = []
        for row in products:
            serializer = InventoryAddressWarehouseSerializer(row)
            result.append({'count': row.plan,
                           'product': serializer.data,
                           'key': row.guid})
        return result

    @staticmethod
    def get_date(obj):
        if obj.external_source is None:
            return obj.date.strftime('%d.%m.%Y')

        try:
            date = dt.strptime(obj.external_source.date, '%Y-%m-%dT%H:%M:%S')
            date = date.strftime('%d.%m.%Y')
        except ValueError:
            date = obj.date.strftime('%d.%m.%Y')
        return date


class InventoryAddressWarehouseWriteSerializer(serializers.Serializer):
    external_source = ExternalSerializer()
    products = InventoryWriteSerializer(many=True)

    class Meta:
        fields = ('external_source', 'products')


class PalletDivideSourceSerializer(serializers.Serializer):
    id = serializers.CharField()


class PalletDivideNewSerializer(serializers.Serializer):
    status = serializers.CharField()
    content_count = serializers.IntegerField()
    id = serializers.CharField()
    weight = serializers.IntegerField(required=False)


class PalletDivideSerializer(serializers.Serializer):
    new_pallet = PalletDivideNewSerializer()
    source_pallet = serializers.CharField()
    type_task = serializers.CharField(required=False)

    def validate(self, attrs):
        instance = Pallet.objects.filter(id=attrs.get('source_pallet')).first()
        if not instance:
            raise APIException('Паллета не найдена')
        if instance.content_count < attrs.get('new_pallet').get('content_count'):
            raise APIException('У разделяемой паллеты не хватает количества')

        return super().validate(attrs)


class ShiftSerializerV4(ShiftSerializer):
    products = serializers.ListField(required=False)
    shift_products = serializers.ListField(required=False)
    type = serializers.CharField()
    production_date = serializers.DateField()
    line = serializers.PrimaryKeyRelatedField(queryset=Line.objects.all())
    batch_number = serializers.CharField()


class CancelShipmentWriteSerializer(serializers.Serializer):

    pallets = serializers.ListField()
    external_source = ExternalSerializer()


class CancelShipmentReadSerializer(serializers.ModelSerializer):

    date = serializers.DateTimeField('%d.%m.%Y')
    number = serializers.CharField()
    pallets = serializers.SerializerMethodField()
    external_source = ExternalSerializer()

    class Meta:
        model = CancelShipmentOperation
        fields = ('guid', 'status', 'date', 'number', 'pallets', 'external_source')

    @staticmethod
    def get_pallets(obj) -> list[dict]:
        operations = OperationCell.objects.filter(operation=obj.guid)
        pallets = []
        for operation in operations:
            serializer_data_pallet = PalletReadSerializer(operation.pallet)
            serializer_data_cell_source = StorageCellsSerializer(operation.cell_source)

            row = {
                'pallet': dict(serializer_data_pallet.data),
                'cell': dict(serializer_data_cell_source.data)
            }
            pallets.append(row)

        return pallets


class PalletMovementShipmentSerializer(serializers.Serializer):
    """ Сериализатор паллеты перемещения под отгрузку """

    pallet = serializers.CharField()
    cell_source = serializers.CharField(source='cell')
    cell_destination = serializers.CharField()
    count = serializers.IntegerField()

    def validate(self, attrs):
        pallet, cell_source, cell_destination = (
            attrs.get('pallet'), attrs.get('cell'), attrs.get('cell_destination')
        )

        if not Pallet.objects.filter(id=pallet).exists():
            raise serializers.ValidationError({'pallet': f'Паллета "{pallet}" не найдена'})

        cells_ext_key = {'cell_source': cell_source, 'cell_destination': cell_destination}
        cells_queryset = StorageCell.objects.filter(external_key__in=[cell_source, cell_destination])

        for key, value in cells_ext_key.items():
            if not cells_queryset.filter(external_key=value).exists():
                raise serializers.ValidationError({key: f'Ячейка "{value}" не найдена'})

        return attrs


class MovementShipmentWriteSerializer(serializers.Serializer):
    """ Сериализатор на запись по операции 'Отмена на перемещение' """

    pallets = PalletMovementShipmentSerializer(many=True)
    external_source = ExternalSerializer()


class MovementShipmentReadSerializer(serializers.ModelSerializer):
    """ Сериализатор на чтение по операции 'Отмена на перемещение' """

    pallets = serializers.SerializerMethodField()
    external_key = serializers.CharField(source='external_source.external_key')

    class Meta:
        model = MovementShipmentOperation
        fields = ('guid', 'status', 'date', 'number', 'pallets', 'external_key')

    @staticmethod
    def get_pallets(obj: MovementShipmentOperation):
        pallets = []
        operations_cell = OperationCell.objects.filter(operation=obj.guid)
        operations_pallet = OperationPallet.objects.filter(operation=obj.guid)
        if not operations_cell.exists() or not operations_pallet.exists():
            return pallets

        for operation_cell in operations_cell:
            operation_pallet = operations_pallet.filter(pallet=operation_cell.pallet).first()

            pallet_serializer = PalletReadSerializer(operation_cell.pallet)

            dependent_pallet = None
            if operation_pallet.dependent_pallet:
                dependent_pallet_serializer = PalletReadSerializer(operation_pallet.dependent_pallet)
                dependent_pallet = dict(dependent_pallet_serializer.data)

            cell_source_serializer = StorageCellsSerializer(operation_cell.cell_source)
            cell_destination_serializer = StorageCellsSerializer(operation_cell.cell_destination)

            pallets.append({
                'pallet':  dict(pallet_serializer.data),
                'cell_source': dict(cell_source_serializer.data),
                'cell_destination': dict(cell_destination_serializer.data),
                'dependent_pallet': dependent_pallet,
                'count': operation_pallet.count
            })

        return pallets
