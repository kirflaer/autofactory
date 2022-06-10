from rest_framework import serializers

from catalogs.models import ExternalSource


class ExternalSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'external_key', 'number', 'date')
        model = ExternalSource
