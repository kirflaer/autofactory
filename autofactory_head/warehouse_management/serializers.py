from rest_framework import serializers

from api.serializers import StorageSerializer
from catalogs.serializers import ExternalSerializer
from warehouse_management.models import (AcceptanceOperation, OperationProduct, PalletCollectOperation, OperationPallet,
                                         Pallet, PlacementToCellsOperation, OperationCell,
                                         MovementBetweenCellsOperation, ShipmentOperation, OrderOperation)


class PalletWriteSerializer(serializers.Serializer):
    codes = serializers.ListField(required=False)
    id = serializers.CharField()
    product = serializers.CharField()
    batch_number = serializers.CharField(required=False)
    production_date = serializers.DateField(required=False)
    content_count = serializers.IntegerField(required=False)
    weight = serializers.IntegerField(required=False)


class PalletReadSerializer(serializers.Serializer):
    id = serializers.CharField()
    product_name = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name', source='product')
    product_guid = serializers.SlugRelatedField(many=False, read_only=True, slug_field='pk', source='product')
    status = serializers.CharField()
    creation_date = serializers.DateTimeField(format="%d.%m.%Y")
    batch_number = serializers.CharField()
    weight = serializers.IntegerField()
    count = serializers.IntegerField(source='content_count')
    production_date = serializers.DateField(format="%d.%m.%Y")
    guid = serializers.UUIDField()


class PalletUpdateSerializer(serializers.ModelSerializer):
    content_count = serializers.IntegerField(required=False)
    id = serializers.CharField(required=False)

    class Meta:
        fields = ('status', 'content_count', 'id')
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
    storage = serializers.CharField()
    production_date = serializers.CharField(required=False)
    batch_number = serializers.CharField(required=False)

    class Meta:
        fields = ('external_source', 'products', 'pallets', 'storage', 'production_date', 'batch_number')


class AcceptanceOperationReadSerializer(serializers.ModelSerializer):
    """ Приемка на склад. Сериализатор для читающих запросов """
    products = serializers.SerializerMethodField()
    storage = StorageSerializer()
    production_date = serializers.DateField(format="%d.%m.%Y")
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    pallets = serializers.SerializerMethodField()
    pallets_count = serializers.SerializerMethodField()
    external_source = ExternalSerializer()

    class Meta:
        model = AcceptanceOperation
        fields = ('guid', 'number', 'status', 'date', 'storage', 'production_date', 'products', 'pallets',
                  'pallets_count', 'batch_number', 'external_source')

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


class MovementCellContent(serializers.Serializer):
    product = serializers.CharField()
    cell = serializers.CharField()
    changed_cell = serializers.CharField()


class MovementBetweenCellsOperationWriteSerializer(serializers.Serializer):
    cells = MovementCellContent(many=True)


class MovementBetweenCellsOperationReadSerializer(serializers.ModelSerializer):
    cells = serializers.SerializerMethodField()
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")

    class Meta:
        model = MovementBetweenCellsOperation
        fields = ('guid', 'number', 'status', 'date', 'cells')

    @staticmethod
    def get_cells(obj):
        cells = OperationCell.objects.filter(operation=obj.guid)
        result = []
        for element in cells:
            result.append(
                {'cell': element.cell.guid if element.cell is not None else None,
                 'changed_cell': element.changed_cell.guid if element.changed_cell is not None else None,
                 'product': element.product.guid if element.product is not None else None
                 })
        return result


class ShipmentOperationReadSerializer(serializers.ModelSerializer):
    direction = serializers.SlugRelatedField(slug_field='name', read_only=True)
    external_source = ExternalSerializer()

    class Meta:
        model = ShipmentOperation
        fields = ('direction', 'external_source', 'guid')


class OrderOperationReadSerializer(serializers.ModelSerializer):
    client = serializers.SlugRelatedField(slug_field='name', read_only=True)
    external_source = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = OrderOperation
        fields = ('client', 'external_source', 'guid')


class PalletProductSerializer(OperationBaseSerializer):
    product = serializers.CharField()
    weight = serializers.FloatField()
    count = serializers.FloatField()
    batch_number = serializers.IntegerField()
    production_date = serializers.DateField()

    class Meta:
        fields = ('product', 'weight', 'count', 'batch_number', 'production_date')


class OrderOperationWriteSerializer(OperationBaseSerializer):
    parent_task = serializers.CharField()
    client = serializers.CharField()
    products = PalletProductSerializer(many=True)

    class Meta:
        fields = ('client', 'external_source', 'guid', 'parent_task')
