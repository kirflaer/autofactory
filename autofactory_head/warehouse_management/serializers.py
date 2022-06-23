from rest_framework import serializers

from api.serializers import ProductShortSerializer, StorageSerializer
from catalogs.serializers import ExternalSerializer
from tasks.serialisers import TaskPropertiesSerializer
from warehouse_management.models import (AcceptanceOperation, OperationProduct, PalletCollectOperation, OperationPallet,
                                         Pallet, PalletContent, PlacementToCellsOperation, OperationCell)


class PalletWriteSerializer(serializers.Serializer):
    codes = serializers.ListField(required=False)
    id = serializers.CharField()
    product = serializers.CharField()
    batch_number = serializers.CharField(required=False)
    production_date = serializers.DateField(required=False)
    content_count = serializers.IntegerField(required=False)


class PalletReadSerializer(serializers.Serializer):
    codes = serializers.SerializerMethodField()
    id = serializers.CharField()
    product = ProductShortSerializer()
    status = serializers.CharField()
    batch_number = serializers.CharField()
    weight = serializers.IntegerField()
    production_date = serializers.DateField(format="%d.%m.%Y")

    @staticmethod
    def get_codes(obj):
        pallet_codes = PalletContent.objects.filter(pallet=obj)
        if pallet_codes.exists():
            return [i.aggregation_code for i in pallet_codes]
        else:
            return []


class PalletUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('status',)
        model = Pallet


class OperationBaseSerializer(serializers.Serializer):
    external_source = ExternalSerializer()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class OperationProductsSerializer(serializers.Serializer):
    product = serializers.CharField()
    weight = serializers.FloatField(required=False)
    count = serializers.FloatField(required=False)

    class Meta:
        fields = ('product', 'weight', 'count')


class OperationCellsSerializer(serializers.Serializer):
    product = serializers.CharField()
    cell = serializers.CharField()
    count = serializers.FloatField(required=False)

    class Meta:
        fields = ('product', 'cell', 'count')


class PalletCollectOperationWriteSerializer(serializers.Serializer):
    pallets = PalletWriteSerializer(many=True)

    class Meta:
        fields = 'pallets',


class PalletShortSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(many=False, read_only=True, slug_field='external_key')

    class Meta:
        model = Pallet
        fields = ('id', 'product', 'content_count', 'batch_number', 'production_date')


class PalletCollectOperationReadSerializer(serializers.ModelSerializer):
    pallets_semi = serializers.SerializerMethodField()
    pallets_complete = serializers.SerializerMethodField()

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'pallets_semi', 'pallets_complete')

    @staticmethod
    def get_pallets_complete(obj):
        return PalletCollectOperationReadSerializer.get_pallets_data(obj.guid, False)

    @staticmethod
    def get_pallets_semi(obj):
        return PalletCollectOperationReadSerializer.get_pallets_data(obj.guid, True)

    @staticmethod
    def get_pallets_data(operation, semi_product):
        pallets_ids = OperationPallet.objects.filter(operation=operation,
                                                     pallet__product__semi_product=semi_product).values_list(
            'pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallets_ids)
        serializer = PalletShortSerializer(pallets, many=True)
        return serializer.data


class AcceptanceOperationWriteSerializer(OperationBaseSerializer):
    products = OperationProductsSerializer(many=True)
    pallets = serializers.ListField()
    storage = serializers.CharField(required=False)
    production_date = serializers.CharField(required=False)
    batch_number = serializers.CharField(required=False)

    class Meta:
        fields = ('external_source', 'products', 'pallets', 'storage', 'production_date', 'batch_number')


class AcceptanceOperationReadSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    storage = StorageSerializer()
    production_date = serializers.DateField(format="%d.%m.%Y")
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    pallets = serializers.SerializerMethodField()
    pallets_count = serializers.SerializerMethodField()

    class Meta:
        model = AcceptanceOperation
        fields = ('guid', 'number', 'status', 'date', 'storage', 'production_date', 'products', 'pallets',
                  'pallets_count', 'batch_number')

    @staticmethod
    def get_pallets_count(obj):
        return OperationPallet.objects.filter(operation=obj.guid).count()

    @staticmethod
    def get_pallets(obj):
        pallets_ids = OperationPallet.objects.filter(operation=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallets_ids)
        serializer = PalletReadSerializer(pallets, many=True)
        return serializer.data

    @staticmethod
    def get_products(obj):
        products = OperationProduct.objects.filter(operation=obj.guid)
        result = []
        for element in products:
            result.append(
                {'name': element.product.name,
                 'weight': element.weight,
                 'guid': element.product.guid,
                 'gtin': element.product.gtin,
                 'count': element.count,
                 })
        return result


class PlacementToCellsOperationWriteSerializer(OperationBaseSerializer):
    cells = OperationCellsSerializer(many=True)
    storage = serializers.CharField(required=False)


class PlacementToCellsOperationReadSerializer(serializers.ModelSerializer):
    storage = StorageSerializer()
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    cells = serializers.SerializerMethodField()

    class Meta:
        model = PlacementToCellsOperation
        fields = ('guid', 'number', 'status', 'date', 'storage', 'cells')

    @staticmethod
    def get_cells(obj):
        cells = OperationCell.objects.filter(operation=obj.guid)
        result = []
        for element in cells:
            result.append(
                {'cell': element.cell.guid if element.cell is not None else None,
                 'changed_cell': element.changed_cell.guid if element.changed_cell is not None else None,
                 'count': element.count,
                 'product': element.product.guid if element.product is not None else None
                 })
        return result
