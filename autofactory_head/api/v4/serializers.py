from rest_framework import serializers
from rest_framework.exceptions import APIException

from factory_core.models import Shift
from warehouse_management.serializers import PalletWriteSerializer


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
