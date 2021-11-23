from abc import ABC
from packing.marking_services import get_base64_string
from rest_framework import serializers
from rest_framework.exceptions import APIException
from django.contrib.auth import get_user_model
from users.models import Setting
from packing.models import MarkingOperation, CollectingOperation

from catalogs.models import (
    Organization,
    Product,
    Device,
    Line,
    Department,
    Storage,
    Unit,
    Log
)

User = get_user_model()


class ConfirmUnloadingSerializer(serializers.Serializer):
    operations = serializers.ListField()

    def validate(self, attrs):
        for operation in attrs.get('operations'):
            if not MarkingOperation.objects.filter(guid=operation).exists():
                raise APIException('Операция маркировки не обнаружена')
        return super().validate(attrs)


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


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'guid')
        model = Organization


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'is_default', 'guid', 'capacity', 'count_in_pallet')
        model = Unit

    def create(self, validated_data):
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True)
    external_key = serializers.CharField(write_only=True, required=False)

    class Meta:
        fields = ('name',
                  'gtin', 'guid', 'is_weight', 'expiration_date', 'units',
                  'external_key')
        model = Product
        read_only_fields = ('guid',)

    def create(self, validated_data):
        units = validated_data.pop('units')
        product = Product.objects.create(**validated_data)
        for unit in units:
            Unit.objects.create(product=product, **unit)
        return product


class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('guid', 'name')
        model = Storage


class DepartmentSerializer(serializers.ModelSerializer):
    external_key = serializers.CharField(write_only=True, required=False)

    class Meta:
        fields = ('guid', 'name', 'external_key')
        read_only_fields = ('guid',)
        model = Department


class LineSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(many=True,
                                                  read_only=True)

    class Meta:
        fields = (
            'guid', 'name', 'storage', 'department', 'products')
        model = Line


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('guid', 'name', 'identifier', 'port')
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

    class Meta:
        fields = ('use_organization', 'pallet_passport_template_base64')
        model = Setting

    def get_pallet_passport_template_base64(self, obj):
        return get_base64_string(obj.pallet_passport_template)


class UserSerializer(serializers.ModelSerializer):
    scanner = DeviceSerializer(read_only=True)
    vision_controller = VisionControllerSerializer(read_only=True)
    device = serializers.SlugRelatedField(many=False, read_only=True,
                                          slug_field='identifier')
    settings = SettingSerializer(read_only=True)

    class Meta:
        fields = (
            'line', 'role', 'device', 'scanner', 'vision_controller',
            'settings')

        model = User


class AggregationsSerializer(serializers.Serializer):
    aggregation_code = serializers.CharField(required=False)
    product = serializers.CharField(required=False)
    marks = serializers.ListField()


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


class CollectingOperationSerializer(serializers.Serializer):
    codes = serializers.ListField()
    identifier = serializers.CharField()
