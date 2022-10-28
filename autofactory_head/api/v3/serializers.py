from rest_framework import serializers

from api.serializers import MarkingSerializer, AggregationsSerializer
from catalogs.models import Product
from factory_core.models import ShiftProduct, Shift
from packing.models import MarkingOperation


class MarkingSerializerOnline(MarkingSerializer):
    shift = serializers.CharField(required=True)

    class Meta:
        fields = (
            'batch_number', 'production_date', 'product', 'organization',
            'guid', 'closed', 'line', 'organization', 'product', 'unloaded', 'weight', 'shift')
        read_only_fields = ('guid', 'closed', 'unloaded')
        model = MarkingOperation


class MarkingSerializerOffline(MarkingSerializer):
    group_offline = serializers.CharField(required=True)
    aggregations = AggregationsSerializer(required=True, many=True, write_only=True)

    class Meta:
        fields = (
            'batch_number', 'production_date', 'product', 'organization', 'line', 'organization', 'product', 'weight',
            'group_offline', 'aggregations')
        model = MarkingOperation


class ShiftSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    line_products = serializers.ListField(write_only=True)

    class Meta:
        model = Shift
        fields = ('guid', 'line', 'batch_number', 'production_date', 'code_offline', 'products', 'line_products')
        read_only_fields = ('guid', 'line', 'batch_number', 'production_date', 'code_offline', 'products')

    @staticmethod
    def get_products(obj):
        return ShiftProduct.objects.filter(shift=obj).values_list('product__guid', flat=True)

    def update(self, instance, validated_data):
        for product_guid in validated_data['line_products']:
            product = Product.objects.filter(guid=product_guid).first()
            if product is None:
                continue
            if ShiftProduct.objects.filter(shift=instance, product=product).exists():
                continue
            ShiftProduct.objects.create(shift=instance, product=product)
        return super().update(instance, validated_data)
