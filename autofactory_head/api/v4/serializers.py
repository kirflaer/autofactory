from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException

from api.v1.serializers import PalletCollectShipmentSerializer, ShipmentOperationReadSerializer, \
    PalletShipmentSerializer
from api.v4.services import prepare_pallet_collect_to_exchange
from catalogs.serializers import ExternalSerializer
from factory_core.models import Shift
from warehouse_management.models import (
    ShipmentOperation, PalletCollectOperation, OperationPallet, Pallet, PalletStatus, PalletProduct,
    SuitablePallets, WriteOffOperation, PalletSource, TypeCollect, InventoryAddressWarehouseOperation,
    InventoryAddressWarehouseContent
)
from warehouse_management.serializers import PalletWriteSerializer, PalletProductSerializer, SuitablePalletSerializer, \
    OperationPalletSerializer, PalletSourceReadSerializer, PalletReadSerializer, InventoryAddressWarehouseSerializer


class PalletCollectOperationWriteSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

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
    pallets = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()

    class Meta:
        model = WriteOffOperation
        fields = ('guid', 'date', 'number', 'status', 'pallets', 'sources')

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


class PalletUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('status',)
        model = Pallet

    def update(self, instance, validated_data):
        with transaction.atomic():
            prepare_pallet_collect_to_exchange(instance)
        return super().update(instance, validated_data)


class InventoryAddressWarehouseReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryAddressWarehouseOperation
        fields = (
            'date', 'guid', 'user', 'number', 'external_source', 'status', 'closed', 'ready_to_unload', 'unloaded'
        )


class InventoryAddressWarehouseWriteSerializer(serializers.Serializer):
    external_source = ExternalSerializer()
    products = InventoryAddressWarehouseSerializer(many=True)

    class Meta:
        fields = ('external_source', 'products')
