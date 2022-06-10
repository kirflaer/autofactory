from rest_framework import serializers


class OperationSerializer(serializers.Serializer):
    date = serializers.DateField()
    number = serializers.CharField()
    guid = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
