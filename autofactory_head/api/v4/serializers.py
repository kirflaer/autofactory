from rest_framework import serializers
from rest_framework.exceptions import APIException

from api.v1.serializers import PalletCollectShipmentSerializer, ShipmentOperationReadSerializer, \
    PalletShipmentSerializer
from factory_core.models import Shift
from warehouse_management.models import ShipmentOperation, PalletCollectOperation, OperationPallet, Pallet, \
    PalletStatus, PalletProduct, SuitablePallets
from warehouse_management.serializers import PalletWriteSerializer, PalletProductSerializer, SuitablePalletSerializer


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

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'date', 'number', 'status', 'pallets', 'user', 'is_owner')

    @staticmethod
    def get_pallets(obj):
        pallet_guids = OperationPallet.objects.filter(operation=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallet_guids, status=PalletStatus.WAITED)
        serializer = PalletShipmentSerializer(pallets, many=True)
        return serializer.data
