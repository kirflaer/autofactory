from rest_framework import serializers
from rest_framework.exceptions import APIException

from api.serializers import StorageSerializer
from catalogs.models import ExternalSource, Product
from catalogs.serializers import ExternalSerializer
from warehouse_management.models import (AcceptanceOperation, OperationProduct, PalletCollectOperation, OperationPallet,
                                         Pallet, PlacementToCellsOperation,
                                         MovementBetweenCellsOperation, ShipmentOperation, OrderOperation,
                                         PalletProduct, PalletStatus, PalletSource, OperationCell)


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
    product = serializers.CharField()
    weight = serializers.FloatField()
    count = serializers.FloatField()
    batch_number = serializers.IntegerField(required=False)
    production_date = serializers.DateField(required=False)
    external_key = serializers.CharField(required=False)
    order = OrderOperationReadSerializer(required=False)
    order_external_source = OrderOperationWriteSerializer(required=False)
    is_weight = serializers.SerializerMethodField(read_only=True, required=False)

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

    def validate(self, attrs):
        pallet_source = Pallet.objects.filter(guid=attrs.get('pallet_source')).first()
        if not pallet_source:
            raise APIException("Не найдена паллета указанная в качестве источника")

        return super().validate(attrs)


class PalletSourceReadSerializer(serializers.ModelSerializer):
    pallet = serializers.SlugRelatedField(slug_field='id', source='pallet_source', read_only=True)

    class Meta:
        fields = ('product', 'batch_number', 'weight', 'count', 'pallet', 'production_date')
        model = PalletSource


class PalletWriteSerializer(serializers.Serializer):
    codes = serializers.ListField(required=False)
    id = serializers.CharField()
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
    external_key = serializers.CharField(read_only=True)

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

    class Meta:
        fields = ('status', 'content_count', 'id', 'sources', 'weight')
        model = Pallet

    def update(self, instance, validated_data):
        if validated_data.get('sources') is not None:
            sources = validated_data.pop('sources')
            for source in sources:
                source['pallet_source'] = Pallet.objects.filter(guid=source['pallet_source']).first()
                source['pallet'] = instance
                source['product'] = Product.objects.filter(guid=source['product']).first()
                PalletSource.objects.create(**source)

        return super().update(instance, validated_data)


class OperationProductsSerializer(serializers.Serializer):
    product = serializers.CharField()
    weight = serializers.FloatField(required=False)
    count = serializers.FloatField(required=False)

    class Meta:
        fields = ('product', 'weight', 'count')


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

    class Meta:
        model = Pallet
        fields = ('id', 'product', 'content_count', 'batch_number', 'production_date', 'status')


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

    class Meta:
        model = ShipmentOperation
        fields = ('direction', 'external_source', 'pallets')


class ShipmentOperationReadSerializer(serializers.ModelSerializer):
    direction_name = serializers.SlugRelatedField(slug_field='name', read_only=True, source='direction')
    date = serializers.SlugRelatedField(slug_field='date', read_only=True, source='external_source')
    number = serializers.SlugRelatedField(slug_field='number', read_only=True, source='external_source')
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')

    class Meta:
        model = ShipmentOperation
        fields = ('direction_name', 'date', 'number', 'guid', 'external_key')


class PalletShipmentSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()

    class Meta:
        model = Pallet
        fields = (
            'id', 'external_key', 'weight', 'content_count', 'pallet_type', 'has_shipped_products', 'weight',
            'products', 'sources')

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

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'date', 'number', 'status', 'pallets')

    @staticmethod
    def get_pallets(obj):
        pallet_guids = OperationPallet.objects.filter(operation=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallet_guids, status=PalletStatus.WAITED)
        serializer = PalletShipmentSerializer(pallets, many=True)
        return serializer.data
