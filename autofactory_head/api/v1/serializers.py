from rest_framework import serializers

from warehouse_management.models import PalletCollectOperation, OperationPallet, Pallet, PalletStatus, PalletProduct, \
    PalletSource, ShipmentOperation
from warehouse_management.serializers import PalletProductSerializer, PalletSourceReadSerializer
from datetime import datetime as dt


class ShipmentOperationReadSerializer(serializers.ModelSerializer):
    number = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')

    class Meta:
        model = ShipmentOperation
        fields = ('direction', 'date', 'number', 'guid', 'external_key', 'has_selection', 'manager')

    @staticmethod
    def get_number(obj):
        return obj.external_source.number.lstrip('0')

    @staticmethod
    def get_date(obj):
        try:
            date = dt.strptime(obj.external_source.date, '%Y-%m-%dT%H:%M:%S')
            date = date.strftime('%d.%m.%Y')
        except ValueError:
            date = obj.date.strftime('%d.%m.%Y')
        return date


class PalletShipmentSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()

    class Meta:
        model = Pallet
        fields = (
            'id', 'external_key', 'weight', 'content_count', 'pallet_type', 'weight', 'status',
            'guid', 'products', 'sources', 'name', 'consignee')

    @staticmethod
    def get_products(obj):
        products = PalletProduct.objects.filter(pallet=obj)
        serializer = PalletProductSerializer(products, many=True)
        return serializer.data

    @staticmethod
    def get_sources(obj):
        sources = PalletSource.objects.filter(pallet=obj)
        serializer = PalletSourceReadSerializer(sources, many=True)
        return serializer.data


class PalletCollectShipmentSerializer(serializers.ModelSerializer):
    pallets = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'date', 'number', 'status', 'pallets', 'user', 'is_owner')

    def get_is_owner(self, instance):
        return self.root.request_user == instance.user

    @staticmethod
    def get_pallets(obj):
        pallet_guids = OperationPallet.objects.filter(operation=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallet_guids, status=PalletStatus.WAITED)
        serializer = PalletShipmentSerializer(pallets, many=True)
        return serializer.data
