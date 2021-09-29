from abc import ABC

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from catalogs.models import Organization, Product, Device
from factory_core.models import ShiftOperation
from rest_framework.exceptions import APIException


class RawDeviceData(serializers.Serializer):
    device = serializers.CharField()
    interval = serializers.CharField(required=False)
    marks = serializers.ListField(required=False)

    def validate(self, attrs):
        if not Device.objects.filter(external_key=attrs['device']).exists():
            raise APIException("Устройство не обнаружено")
        return super().validate(attrs)


class ShiftOpenSerializer(serializers.ModelSerializer):
    number = serializers.CharField(source='batch_number')
    date = serializers.CharField()
    catalog = serializers.CharField(source='product')

    class Meta:
        fields = ('organization', 'number', 'date', 'catalog')
        model = ShiftOperation

    # def validate(self, attrs):
    #     author = self.context['request'].user
    #     if ShiftOperation.objects.filter(author=author, closed=False).exists():
    #         raise APIException("Смена уже открыта")
    #     return super().validate(attrs)


class ShiftSerializer(serializers.ModelSerializer):
    part = serializers.CharField(source='batch_number')
    date = serializers.DateField(source='production_date',
                                 format="%d.%m.%Y")
    catalog_name = serializers.CharField(source='product')

    class Meta:
        fields = ('guid', 'part', 'date', 'catalog_name')
        model = ShiftOperation


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'guid')
        model = Organization


class ProductSerializer(serializers.ModelSerializer):
    countInPallet = serializers.CharField(source='count_in_pallet')
    expData = serializers.CharField(source='expiration_date')

    class Meta:
        fields = ('name', 'sku', 'guid', 'expData', 'countInPallet')
        model = Product
