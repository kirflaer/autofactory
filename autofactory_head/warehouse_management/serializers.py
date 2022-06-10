from rest_framework import serializers

from api.serializers import PalletWriteSerializer
from catalogs.serializers import ExternalSerializer
from warehouse_management.models import MovementOperation, OperationProduct


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


class MovementOperationWriteSerializer(OperationBaseSerializer):
    products = OperationProductsSerializer(many=True)
    pallets = serializers.ListField()

    class Meta:
        fields = ('external_source', 'products', 'pallets')


class MovementOperationReadSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = MovementOperation
        fields = ('guid', 'number', 'status', 'date', 'products')

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

# class TaskUpdateSerializer(serializers.ModelSerializer):
#     pallet_ids = serializers.ListField(required=False)
#     unloaded = serializers.BooleanField(required=False)
#     ready_to_unload = serializers.BooleanField(required=False)
#     status = serializers.CharField(required=False)
#
#     class Meta:
#         fields = ('status', 'pallet_ids', 'unloaded', 'ready_to_unload')
#         model = Task


# class TaskPalletSerializer(serializers.ModelSerializer):
#     product_name = serializers.StringRelatedField(read_only=True,
#                                                   source='product')
#     count = serializers.SerializerMethodField()
#
#     class Meta:
#         fields = ('id', 'is_confirmed', 'product_name', 'count', 'guid')
#         model = Pallet
#
#     def get_count(self, obj):
#         return PalletCode.objects.filter(pallet__pk=obj.guid).count()
#
#
# class TaskWriteSerializer(serializers.Serializer):
#     pallets = serializers.ListField(required=False)
#     products = TaskProductsSerializer(many=True, required=False)
#
#     direction = DirectionSerializer(required=False)
#
#     class Meta:
#         fields = (
#             'type_task', 'products', 'pallets', 'external_source', 'client',
#             'direction', 'parent_task')
#
#
# class TaskReadSerializer(serializers.ModelSerializer):
#     products = serializers.SerializerMethodField()
#     pallets = TaskPalletSerializer(many=True, read_only=True)
#     external_source = ExternalSerializer(required=False)
#     direction_name = serializers.StringRelatedField(read_only=True,
#                                                     source='direction')
#     client_name = serializers.StringRelatedField(read_only=True,
#                                                  source='client')
#
#     class Meta:
#         fields = (
#             'guid', 'number', 'status', 'date', 'products', 'pallets',
#             'client_name', 'direction_name', 'type_task', 'external_source')
#
#         model = Task
#
#     def get_products(self, obj):
#         task_products = TaskProduct.objects.filter(task__guid=obj.guid)
#         result = []
#         if not task_products.exists():
#             return result
#         for element in task_products:
#             result.append(
#                 {'name': element.product.name,
#                  'weight': element.weight,
#                  'guid': element.product.guid,
#                  'gtin': element.product.gtin,
#                  'count': element.count,
#                  })
#         return result
