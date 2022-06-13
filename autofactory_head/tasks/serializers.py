from rest_framework import serializers
from rest_framework.exceptions import APIException

from .models import TaskStatus


class TaskUpdateSerializer(serializers.Serializer):
    status = serializers.CharField()

    class Meta:
        fields = ('status',)

    def validate(self, attrs):
        if not attrs.get('status').upper() in TaskStatus:
            raise APIException('Переданный статус не найден')
        return super().validate(attrs)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
