from rest_framework import serializers

# TODO убрать зависимость от модуля api
from api.serializers import PalletWriteSerializer, StorageSerializer, PalletReadSerializer
from catalogs.serializers import ExternalSerializer
from warehouse_management.models import AcceptanceOperation, OperationProduct, PalletCollectOperation, OperationPallet, \
    Pallet


class OperationBaseSerializer(serializers.Serializer):
    external_source = ExternalSerializer(required=False)

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

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class PalletCollectOperationWriteSerializer(serializers.Serializer):
    pallets = PalletWriteSerializer(many=True)

    class Meta:
        fields = 'pallets',

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class PalletCollectOperationReadSerializer(serializers.ModelSerializer):
    pallets = serializers.SerializerMethodField()

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'pallets')

    @staticmethod
    def get_pallets(obj):
        pallets = OperationPallet.objects.filter(operation=obj.guid)
        result = []
        for element in pallets:
            result.append(
                {'product': element.pallet.product.external_key,
                 'count': element.pallet.content_count,
                 'batch_number': element.pallet.batch_number,
                 'production_date': element.pallet.production_date,
                 })
        return result


class AcceptanceOperationWriteSerializer(OperationBaseSerializer):
    products = OperationProductsSerializer(many=True)
    pallets = serializers.ListField()
    storage = serializers.CharField(required=False)
    production_date = serializers.CharField(required=False)

    class Meta:
        fields = ('external_source', 'products', 'pallets', 'storage', 'production_date')


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
