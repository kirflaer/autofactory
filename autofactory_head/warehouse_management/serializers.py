from rest_framework import serializers
from rest_framework.exceptions import APIException

from api.serializers import StorageSerializer
from catalogs.models import ExternalSource, Product
from catalogs.serializers import ExternalSerializer
from warehouse_management.models import (AcceptanceOperation, OperationProduct, PalletCollectOperation, OperationPallet,
                                         Pallet, PlacementToCellsOperation, OperationCell,
                                         MovementBetweenCellsOperation, ShipmentOperation, OrderOperation,
                                         PalletProduct, PalletStatus, PalletSource)


class OperationBaseSerializer(serializers.Serializer):
    external_source = ExternalSerializer()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class PalletProductSerializer(serializers.Serializer):
    product = serializers.CharField()
    weight = serializers.FloatField()
    count = serializers.FloatField()
    batch_number = serializers.IntegerField()
    production_date = serializers.DateField()

    class Meta:
        fields = ('product', 'weight', 'count', 'batch_number', 'production_date')


class PalletSourceCreateSerializer(serializers.Serializer):
    pallet = serializers.CharField(source='pallet_source')
    product = serializers.CharField()
    batch_number = serializers.CharField()
    weight = serializers.IntegerField()
    count = serializers.IntegerField()

    def validate(self, attrs):
        pallet_source = Pallet.objects.filter(id=attrs.get('pallet_source')).first()
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

    @staticmethod
    def get_sources(obj):
        sources = PalletSource.objects.filter(pallet=obj)
        serializer = PalletSourceReadSerializer(sources, many=True)
        return serializer.data


class PalletUpdateSerializer(serializers.ModelSerializer):
    content_count = serializers.IntegerField(required=False)
    id = serializers.CharField(required=False)
    sources = PalletSourceCreateSerializer(many=True, required=False)

    class Meta:
        fields = ('status', 'content_count', 'id', 'sources')
        model = Pallet

    def update(self, instance, validated_data):
        if validated_data.get('sources') is not None:
            sources = validated_data.pop('sources')
            for source in sources:
                source['pallet_source'] = Pallet.objects.filter(id=source['pallet_source']).first()
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


class ShipmentOperationWriteSerializer(serializers.ModelSerializer):
    direction = serializers.CharField()
    external_source = ExternalSerializer()

    class Meta:
        model = ShipmentOperation
        fields = ('direction', 'external_source', 'guid')


class ShipmentOperationReadSerializer(serializers.ModelSerializer):
    direction_name = serializers.SlugRelatedField(slug_field='name', read_only=True, source='direction')
    date = serializers.SlugRelatedField(slug_field='date', read_only=True, source='external_source')
    number = serializers.SlugRelatedField(slug_field='number', read_only=True, source='external_source')
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')

    class Meta:
        model = ShipmentOperation
        fields = ('direction_name', 'date', 'number', 'guid', 'external_key')


class OrderOperationReadSerializer(serializers.ModelSerializer):
    client_name = serializers.SlugRelatedField(slug_field='name', read_only=True, source='client')
    date = serializers.SlugRelatedField(slug_field='date', read_only=True, source='external_source')
    number = serializers.SlugRelatedField(slug_field='number', read_only=True, source='external_source')
    pallets = serializers.SerializerMethodField()

    class Meta:
        model = OrderOperation
        fields = ('guid', 'client_name', 'date', 'number', 'status', 'pallets')

    @staticmethod
    def get_pallets(obj):
        pallet_guids = OperationPallet.objects.filter(operation=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallet_guids, status=PalletStatus.WAITED).values('guid',
                                                                                                  'content_count',
                                                                                                  'weight')

        pallets_products = PalletProduct.objects.filter(pallet__in=[pallet['guid'] for pallet in pallets]).values(
            'product', 'count', 'weight', 'batch_number', 'production_date', 'pallet')
        products = {}
        result = []
        for record in pallets_products:
            if not products.get(record['pallet']):
                products[record['pallet']] = []
            products[record['pallet']].append(record)

        for pallet in pallets:
            if products.get(pallet['guid']) is not None:
                pallet['products'] = products[pallet['guid']]

            sources = PalletSource.objects.filter(pallet=pallet['guid'])
            serializer = PalletSourceReadSerializer(sources, many=True)
            pallet['sources'] = serializer.data
            result.append(pallet)

        return result


class OrderOperationWriteSerializer(OperationBaseSerializer):
    parent_task = serializers.CharField()
    client = serializers.CharField()
    pallets = serializers.ListField()

    class Meta:
        fields = ('client', 'external_source', 'guid', 'parent_task', 'pallets')

    def validate(self, attrs):
        parent_task_source = ExternalSource.objects.filter(external_key=attrs.get('parent_task')).first()
        if not parent_task_source:
            raise APIException("Не найден источник родительской задачи")
        if not ShipmentOperation.objects.filter(external_source=parent_task_source).first():
            raise APIException("Не найдена родительская задача")

        return super().validate(attrs)
