from rest_framework import serializers

import api.serializers as api_serializers
from packing.models import MarkingOperation


class MarkingSerializer(api_serializers.MarkingSerializer):
    aggregations = api_serializers.AggregationsSerializer(required=False, many=True)

    class Meta:
        fields = (
            'batch_number', 'production_date', 'product', 'organization',
            'guid', 'closed', 'line', 'organization', 'product',
            'aggregations', 'unloaded', 'weight', 'group', 'group_offline')
        read_only_fields = ('guid', 'closed', 'unloaded')
        model = MarkingOperation
