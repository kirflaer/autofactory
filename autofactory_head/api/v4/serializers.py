from rest_framework import serializers
from rest_framework.exceptions import APIException

from factory_core.models import Shift
from warehouse_management.models import ShipmentOperation, PalletCollectOperation
from warehouse_management.serializers import PalletWriteSerializer, ShipmentOperationReadSerializer, \
    PalletCollectShipmentSerializer


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


class PalletCollectShipmentSerializerV4(PalletCollectShipmentSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field='username')

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'date', 'number', 'status', 'pallets', 'user', 'is_owner')
