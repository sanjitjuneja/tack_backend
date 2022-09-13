from rest_framework import serializers


class NotificationSerializer(serializers.Serializer):
    user = serializers.IntegerField()
