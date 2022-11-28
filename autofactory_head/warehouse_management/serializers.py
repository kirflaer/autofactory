from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException

from api.serializers import StorageSerializer
from catalogs.models import ExternalSource, Product
from catalogs.serializers import ExternalSerializer
from warehouse_management.models import (AcceptanceOperation, OperationProduct, PalletCollectOperation, OperationPallet,
                                         Pallet, PlacementToCellsOperation,
                                         MovementBetweenCellsOperation, ShipmentOperation, OrderOperation,
                                         PalletProduct, PalletStatus, PalletSource, OperationCell, InventoryOperation,
                                         SelectionOperation)
from warehouse_management.warehouse_services import check_and_collect_orders, enrich_pallet_info


class OperationBaseSerializer(serializers.Serializer):
    external_source = ExternalSerializer()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class OrderOperationReadSerializer(serializers.Serializer):
    client_presentation = serializers.CharField()
    number = serializers.CharField()
    date = serializers.DateTimeField(format="%Y-%m-%d")
    guid = serializers.UUIDField()


class OrderOperationWriteSerializer(serializers.ModelSerializer):
    client_presentation = serializers.CharField()

    class Meta:
        fields = ('name', 'external_key', 'number', 'date', 'client_presentation')
        model = ExternalSource


class PalletProductSerializer(serializers.Serializer):
    product = serializers.UUIDField(write_only=True)
    guid = serializers.SlugRelatedField(read_only=True, source='product', slug_field='pk')
    weight = serializers.IntegerField()
    count = serializers.IntegerField()
    batch_number = serializers.IntegerField(required=False)
    production_date = serializers.DateField(required=False)
    external_key = serializers.CharField(required=False)
    order = OrderOperationReadSerializer(required=False)
    order_external_source = OrderOperationWriteSerializer(required=False)
    is_weight = serializers.SerializerMethodField(read_only=True, required=False)
    has_shipped_products = serializers.BooleanField(required=False)
    is_collected = serializers.BooleanField(required=False)

    @staticmethod
    def get_is_weight(obj):
        return obj.product.is_weight


class PalletSourceCreateSerializer(serializers.Serializer):
    pallet = serializers.CharField(source='pallet_source')
    product = serializers.CharField()
    batch_number = serializers.CharField()
    weight = serializers.IntegerField()
    count = serializers.IntegerField()
    production_date = serializers.DateField()
    external_key = serializers.CharField(required=False)

    def validate(self, attrs):
        pallet_source = Pallet.objects.filter(guid=attrs.get('pallet_source')).first()
        if not pallet_source:
            raise APIException("Не найдена паллета указанная в качестве источника")

        return super().validate(attrs)


class PalletSourceReadSerializer(serializers.ModelSerializer):
    pallet = serializers.SlugRelatedField(slug_field='id', source='pallet_source', read_only=True)
    is_weight = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        fields = (
            'product', 'batch_number', 'weight', 'count', 'pallet', 'production_date', 'external_key', 'is_weight')
        model = PalletSource

    @staticmethod
    def get_is_weight(obj):
        return obj.product.is_weight


class PalletWriteSerializer(serializers.Serializer):
    codes = serializers.ListField(required=False)
    id = serializers.CharField(required=False)
    product = serializers.CharField(required=False)
    batch_number = serializers.CharField(required=False)
    production_date = serializers.DateField(required=False)
    content_count = serializers.IntegerField(required=False)
    weight = serializers.IntegerField(required=False)
    external_key = serializers.CharField(required=False)
    products = PalletProductSerializer(many=True, required=False)
    status = serializers.CharField(required=False)
    production_shop = serializers.CharField(required=False)
    pallet_type = serializers.CharField(required=False)
    marking_group = serializers.CharField(required=False)
    shift = serializers.CharField(required=False)
    code_offline = serializers.CharField(required=False)
    cell = serializers.CharField(required=False)


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
    sources = serializers.SerializerMethodField()
    production_shop = serializers.SlugRelatedField(read_only=True, slug_field='pk')
    cell = serializers.SlugRelatedField(read_only=True, slug_field='name')
    external_key = serializers.CharField(read_only=True)
    marking_group = serializers.CharField(required=False)

    @staticmethod
    def get_sources(obj):
        sources = PalletSource.objects.filter(pallet=obj)
        serializer = PalletSourceReadSerializer(sources, many=True)
        return serializer.data


class PalletUpdateSerializer(serializers.ModelSerializer):
    content_count = serializers.IntegerField(required=False)
    id = serializers.CharField(required=False)
    sources = PalletSourceCreateSerializer(many=True, required=False)
    weight = serializers.IntegerField(required=False)
    collected_strings = serializers.ListField(required=False)

    class Meta:
        fields = ('status', 'content_count', 'id', 'sources', 'weight', 'collected_strings')
        model = Pallet

    def update(self, instance, validated_data):
        with transaction.atomic():
            product_keys = []
            enrich_pallet_info(validated_data, product_keys, instance)
            check_and_collect_orders(product_keys)
        return super().update(instance, validated_data)


class OperationProductsSerializer(serializers.Serializer):
    product = serializers.CharField()
    weight = serializers.FloatField(required=False)
    count = serializers.FloatField(required=False)


class OperationCellsSerializer(serializers.Serializer):
    pallet = serializers.CharField()
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
    cell = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name')

    class Meta:
        model = Pallet
        fields = (
            'id', 'guid', 'product', 'content_count', 'batch_number', 'production_date', 'status', 'marking_group',
            'cell')


class PalletCollectOperationReadSerializer(serializers.ModelSerializer):
    pallets_semi = serializers.SerializerMethodField()
    pallets_complete = serializers.SerializerMethodField()
    pallets_not_marked = serializers.SerializerMethodField()

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'pallets_semi', 'pallets_complete', 'pallets_not_marked')

    @staticmethod
    def get_pallets_not_marked(obj):
        return PalletCollectOperationReadSerializer.get_pallets_data({'operation': obj.guid,
                                                                      'pallet__product__not_marked': True})

    @staticmethod
    def get_pallets_complete(obj):
        return PalletCollectOperationReadSerializer.get_pallets_data({'operation': obj.guid,
                                                                      'pallet__product__semi_product': False,
                                                                      'pallet__product__not_marked': False})

    @staticmethod
    def get_pallets_semi(obj):
        return PalletCollectOperationReadSerializer.get_pallets_data({'operation': obj.guid,
                                                                      'pallet__product__semi_product': True})

    @staticmethod
    def get_pallets_data(product_filter):
        pallets_ids = OperationPallet.objects.filter(**product_filter).values_list(
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
                {'cell_source': element.cell_source.guid if element.cell_source is not None else None,
                 'cell_destination': element.cell_destination.guid if element.cell_destination is not None else None,
                 'count': element.count,
                 'pallet': element.pallet.guid if element.pallet is not None else None
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
    def get_cells():
        return []


class ShipmentOperationWriteSerializer(serializers.ModelSerializer):
    direction = serializers.CharField()
    external_source = ExternalSerializer()
    pallets = PalletWriteSerializer(many=True)
    has_selection = serializers.BooleanField(required=False)

    class Meta:
        model = ShipmentOperation
        fields = ('direction', 'external_source', 'pallets', 'has_selection')


class ShipmentOperationReadSerializer(serializers.ModelSerializer):
    direction_name = serializers.SlugRelatedField(slug_field='name', read_only=True, source='direction')
    date = serializers.SlugRelatedField(slug_field='date', read_only=True, source='external_source')
    number = serializers.SlugRelatedField(slug_field='number', read_only=True, source='external_source')
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')

    class Meta:
        model = ShipmentOperation
        fields = ('direction_name', 'date', 'number', 'guid', 'external_key', 'has_selection')


class PalletShipmentSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()

    class Meta:
        model = Pallet
        fields = (
            'id', 'external_key', 'weight', 'content_count', 'pallet_type', 'weight', 'status',
            'guid', 'products', 'sources')

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


class OrderReadSerializer(serializers.ModelSerializer):
    pallets = serializers.SerializerMethodField()
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')

    class Meta:
        model = OrderOperation
        fields = ('guid', 'date', 'number', 'status', 'external_key', 'pallets')

    @staticmethod
    def get_pallets(obj):
        pallet_guids = PalletProduct.objects.filter(order=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallet_guids)
        serializer = PalletShipmentSerializer(pallets, many=True)
        return serializer.data


class ArrivalAtStockOperationWriteSerializer(OperationBaseSerializer):
    products = OperationProductsSerializer(many=True)
    storage = serializers.CharField()

    class Meta:
        fields = ('external_source', 'products', 'storage')


class ArrivalAtStockOperationReadSerializer(serializers.ModelSerializer):
    """ Приход на склад. Сериализатор для читающих запросов """
    products = serializers.SerializerMethodField()
    storage = StorageSerializer()
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    external_source = ExternalSerializer()

    class Meta:
        model = AcceptanceOperation
        fields = ('guid', 'number', 'status', 'date', 'storage', 'products', 'external_source')

    @staticmethod
    def get_products(obj):
        products = OperationProduct.objects.filter(operation=obj.guid)
        serializer = OperationProductsSerializer(products, many=True)
        return serializer.data


class InventoryOperationWriteSerializer(OperationBaseSerializer):
    products = OperationProductsSerializer(many=True)

    class Meta:
        fields = ('external_source', 'products', 'storage')


class OperationInventoryProductsSerializer(serializers.Serializer):
    product = serializers.CharField()
    product_guid = serializers.SlugRelatedField(slug_field='pk', source='product', read_only=True)
    plan = serializers.FloatField(required=False, source='count')
    fact = serializers.FloatField(required=False, source='count_fact')


class InventoryOperationReadSerializer(serializers.ModelSerializer):
    """ Инвентаризация. Сериализатор для читающих запросов """
    products = serializers.SerializerMethodField()
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    external_source = ExternalSerializer()

    class Meta:
        model = InventoryOperation
        fields = ('guid', 'number', 'status', 'date', 'products', 'external_source')

    @staticmethod
    def get_products(obj):
        products = OperationProduct.objects.filter(operation=obj.guid)
        serializer = OperationInventoryProductsSerializer(products, many=True)
        return serializer.data


class SelectionOperationReadSerializer(serializers.ModelSerializer):
    date = serializers.SlugRelatedField(slug_field='date', read_only=True, source='external_source')
    number = serializers.SlugRelatedField(slug_field='number', read_only=True, source='external_source')
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')
    pallets = serializers.SerializerMethodField()

    class Meta:
        model = SelectionOperation
        fields = ('date', 'number', 'guid', 'external_key', 'pallets')

    @staticmethod
    def get_pallets(obj):
        cells = OperationCell.objects.filter(operation=obj.guid).values_list('cell_source', flat=True)

        if not cells.count():
            return []

        pallets = Pallet.objects.filter(cell__in=cells, status=PalletStatus.CONFIRMED)
        serializer = PalletShortSerializer(pallets, many=True)
        return serializer.data


class SelectionOperationWriteSerializer(serializers.ModelSerializer):
    external_source = ExternalSerializer()
    cells = serializers.ListField()

    class Meta:
        model = SelectionOperation
        fields = ('external_source', 'cells')
