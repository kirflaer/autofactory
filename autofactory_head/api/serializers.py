from rest_framework import serializers
from rest_framework.exceptions import APIException
from django.contrib.auth import get_user_model

from packing.models import MarkingOperation

from catalogs.models import (
    Organization,
    Product,
    Device,
    Line,
    Department,
    Storage,
    Unit
)

User = get_user_model()


class ConfirmUnloadingSerializer(serializers.Serializer):
    guids = serializers.ListField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class AggregationsSerializer(serializers.Serializer):
    aggregation_code = serializers.CharField(required=False)
    product = serializers.CharField(required=False)
    marks = serializers.ListField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class MarkingSerializer(serializers.ModelSerializer):
    production_date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        fields = (
            'batch_number', 'production_date', 'product', 'organization',
            'guid', 'closed', 'line')
        read_only_fields = ('guid', 'organization', 'closed')
        model = MarkingOperation


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'guid')
        model = Organization


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'is_default', 'guid', 'capacity', 'count_in_pallet')
        model = Unit


class ProductSerializer(serializers.ModelSerializer):
    units = UnitSerializer(read_only=True, many=True)

    class Meta:
        fields = ('name', 'gtin', 'guid', 'expiration_date', 'units')
        model = Product


class StorageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('guid', 'name')
        model = Storage


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('guid', 'name')
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
        fields = ('guid', 'name', 'identifier', 'port', 'polling_interval')
        read_only_fields = ('guid', 'port', 'polling_interval')
        model = Device


class UserSerializer(serializers.ModelSerializer):
    scanner = DeviceSerializer(read_only=True)

    class Meta:
        fields = ('line', 'role', 'device', 'scanner')
        model = User


