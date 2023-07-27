from rest_framework import serializers

from api.serializers import MarkingSerializer, AggregationsSerializer
from catalogs.models import Product
from factory_core.models import ShiftProduct, Shift
from packing.models import MarkingOperation
from warehouse_management.models import StorageArea, StorageCell
from warehouse_management.serializers import PalletReadSerializer
from warehouse_management.warehouse_services import get_cell_state


class MarkingSerializerOnlineWrite(MarkingSerializer):
    shift = serializers.CharField(required=True, write_only=True)

    class Meta:
        fields = (
            'batch_number', 'production_date', 'product', 'organization',
            'guid', 'closed', 'line', 'organization', 'product', 'unloaded', 'weight', 'shift')
        read_only_fields = ('guid', 'closed', 'unloaded')
        model = MarkingOperation


class MarkingSerializerOnlineRead(MarkingSerializerOnlineWrite):
    shift = serializers.SlugRelatedField(read_only=True, slug_field='pk')


class MarkingSerializerOffline(MarkingSerializer):
    group_offline = serializers.CharField(required=True)
    aggregations = AggregationsSerializer(required=True, many=True, write_only=True)

    class Meta:
        fields = (
            'batch_number', 'production_date', 'product', 'organization', 'line', 'organization', 'product', 'weight',
            'group_offline', 'aggregations')
        model = MarkingOperation


class ShiftSerializer(serializers.ModelSerializer):
    products = serializers.HiddenField(default='')
    shift_products = serializers.ListField(write_only=True)

    class Meta:
        model = Shift
        fields = (
            'guid', 'line', 'batch_number', 'production_date', 'code_offline', 'products', 'shift_products', 'type')
        read_only_fields = ('guid', 'line', 'batch_number', 'production_date', 'code_offline', 'products', 'type')


class ShiftUpdateSerializer(ShiftSerializer):
    products = serializers.ListField()

    def update(self, instance, validated_data):
        for product_guid in validated_data['products']:
            product = Product.objects.filter(guid=product_guid).first()
            if product is None:
                continue
            if ShiftProduct.objects.filter(shift=instance, product=product).exists():
                continue
            ShiftProduct.objects.create(shift=instance, product=product)
        return super().update(instance, validated_data)


class ShiftRetrieveSerializer(ShiftSerializer):
    products = serializers.SerializerMethodField()

    @staticmethod
    def get_products(obj):
        return ShiftProduct.objects.filter(shift=obj).values_list('product__guid', flat=True)


class StorageAreaSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('guid', 'name', 'external_key', 'new_status_on_admission')
        model = StorageArea
        read_only_fields = ('guid', 'new_status_on_admission')


class StorageCellsRetrieveSerializer(serializers.ModelSerializer):
    pallet = serializers.SerializerMethodField()

    class Meta:
        fields = ('guid', 'name', 'external_key', 'barcode', 'needed_scan', 'pallet', 'rack_number', 'position')
        read_only_fields = ('guid', 'name', 'external_key', 'barcode', 'needed_scan', 'pallet')
        model = StorageCell

    @staticmethod
    def get_pallet(obj):
        change_state_row = get_cell_state(cell=obj)
        if change_state_row is None:
            return None

        serializer = PalletReadSerializer(change_state_row.pallet)
        return serializer.data
