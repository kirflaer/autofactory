from rest_framework import serializers

#TODO убрать зависимость от модуля api
from api.serializers import PalletWriteSerializer, StorageSerializer
from catalogs.serializers import ExternalSerializer
from warehouse_management.models import AcceptanceOperation, OperationProduct


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
    production_date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = AcceptanceOperation
        fields = ('guid', 'number', 'status', 'date', 'storage', 'production_date', 'products')

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
