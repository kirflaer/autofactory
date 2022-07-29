from rest_framework import serializers
from rest_framework.exceptions import APIException

from tasks.models import TaskStatus


class TaskPropertiesSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    unloaded = serializers.BooleanField(required=False)

    def validate(self, attrs):
        status = attrs.get('status')
        if status is not None and not status.upper() in TaskStatus:
            raise APIException('Переданный статус не найден')
        return super().validate(attrs)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
