from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import APIException

from catalogs.models import (Client, Department, Device, Direction, Line, Log, Organization, Product, RegularExpression,
                             Storage, TypeFactoryOperation, Unit)
from packing.marking_services import get_base64_string
from packing.models import MarkingOperation
from users.models import Setting
from warehouse_management.models import PalletContent, Pallet

User = get_user_model()


class ConfirmUnloadingSerializer(serializers.Serializer):
    operations = serializers.ListField()

    def validate(self, attrs):
        for operation in attrs.get('operations'):
            if not MarkingOperation.objects.filter(guid=operation).exists():
                raise APIException('Операция маркировки не обнаружена')
        return super().validate(attrs)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class MarksSerializer(serializers.Serializer):
    marks = serializers.ListField()
    marking = serializers.CharField(required=False)

    def validate(self, attrs):
        if self.source == 'post_request':
            if attrs.get('marking') is None:
                raise APIException(
                    'Для POST запроса обязательно указывать marking')
            if not MarkingOperation.objects.filter(
                    guid=attrs.get('marking')).exists():
                raise APIException('Операция маркировки не обнаружена')
            operation = MarkingOperation.objects.get(guid=attrs.get('marking'))
            if operation.unloaded:
                raise APIException('Нельзя изменять выгруженную маркировку')

        return super().validate(attrs)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class TypeFactoryOperationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'external_key')
        model = TypeFactoryOperation


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'guid')
        model = Organization


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'product', 'name', 'is_default', 'guid', 'capacity', 'count_in_pallet', 'gtin')
        model = Unit


class ProductSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True)
    external_key = serializers.CharField(required=False)

    class Meta:
        fields = ('name', 'gtin', 'guid', 'is_weight', 'expiration_date', 'units', 'external_key', 'semi_product')
        model = Product
        read_only_fields = ('guid', 'expiration_date', 'store_semi_product')

    def create(self, validated_data):
        units = validated_data.pop('units')
        product = Product.objects.create(**validated_data)
        for unit in units:
            Unit.objects.create(product=product, **unit)
        return product


class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('guid', 'name', 'store_semi_product')
        model = Storage
        read_only_fields = ('store_semi_product',)


class DepartmentSerializer(serializers.ModelSerializer):
    external_key = serializers.CharField(write_only=True, required=False)

    class Meta:
        fields = ('guid', 'name', 'external_key')
        read_only_fields = ('guid',)
        model = Department


class LineCreateSerializer(serializers.Serializer):
    products = serializers.ListField()
    name = serializers.CharField()
    storage = serializers.CharField(allow_blank=True)
    department = serializers.CharField(allow_blank=True)
    type_factory_operation = serializers.CharField(allow_blank=True)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class LineSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(many=True,
                                                  read_only=True)

    class Meta:
        fields = (
            'guid', 'name', 'storage', 'department', 'products')
        model = Line


class DeviceSerializer(serializers.ModelSerializer):
    activation_key = serializers.CharField(write_only=True, required=False)

    class Meta:
        fields = ('guid', 'name', 'identifier', 'port', 'activation_key')
        read_only_fields = ('guid', 'port')
        model = Device


class VisionControllerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('identifier', 'port')
        model = Device


class LogSerializer(serializers.ModelSerializer):
    data_base64 = serializers.CharField(source="data")

    class Meta:
        fields = ('data_base64', 'app_version')
        model = Log


class SettingSerializer(serializers.ModelSerializer):
    pallet_passport_template_base64 = serializers.SerializerMethodField()
    reg_exp = serializers.SerializerMethodField()

    class Meta:
        fields = ('use_organization', 'pallet_passport_template_base64',
                  'reg_exp')
        model = Setting

    @staticmethod
    def get_pallet_passport_template_base64(obj):
        return get_base64_string(obj.pallet_passport_template)

    @staticmethod
    def get_reg_exp(obj):
        expressions = RegularExpression.objects.filter().values(
            'type_expression', 'value')
        if not expressions.exists():
            return []
        return expressions


class UserSerializer(serializers.ModelSerializer):
    scanner = DeviceSerializer(read_only=True)
    vision_controller = VisionControllerSerializer(read_only=True)
    device = serializers.SlugRelatedField(many=False, read_only=True,
                                          slug_field='identifier')
    settings = SettingSerializer(read_only=True)

    class Meta:
        fields = (
            'pk', 'line', 'role', 'device', 'scanner', 'vision_controller',
            'settings', 'log_level', 'inactive_sound_enabled',
            'inactive_period_in_sec', 'use_aggregations')

        model = User


class AggregationsSerializer(serializers.Serializer):
    aggregation_code = serializers.CharField(required=False)
    product = serializers.CharField(required=False)
    marks = serializers.ListField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class MarkingSerializer(serializers.ModelSerializer):
    aggregations = AggregationsSerializer(required=False, many=True)
    production_date = serializers.DateField(format="%Y-%m-%d")
    product = serializers.CharField(write_only=True, required=False)
    organization = serializers.CharField(write_only=True, required=False)

    class Meta:
        fields = (
            'batch_number', 'production_date', 'product', 'organization',
            'guid', 'closed', 'line', 'organization', 'product',
            'aggregations', 'unloaded')
        read_only_fields = ('guid', 'closed', 'unloaded')
        model = MarkingOperation


class ProductShortSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'gtin', 'guid')
        model = Product


class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'guid', 'external_key')
        read_only_fields = ('guid',)
        model = Direction


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'external_key')
        model = Client


class RegularExpressionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('value', 'type_expression')
        model = RegularExpression


class PalletWriteSerializer(serializers.Serializer):
    codes = serializers.ListField()
    id = serializers.CharField()
    product = serializers.CharField()
    batch_number = serializers.CharField(required=False)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class PalletReadSerializer(serializers.Serializer):
    codes = serializers.SerializerMethodField()
    id = serializers.CharField()
    product = ProductShortSerializer()
    status = serializers.CharField()
    batch_number = serializers.CharField()
    weight = serializers.IntegerField()
    production_date = serializers.DateField(format="%Y-%m-%d")

    @staticmethod
    def get_codes(obj):
        pallet_codes = PalletContent.objects.filter(pallet=obj)
        if pallet_codes.exists():
            return [i.aggregation_code for i in pallet_codes]
        else:
            return []

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class PalletUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('status',)
        model = Pallet
