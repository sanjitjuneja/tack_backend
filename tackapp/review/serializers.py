from rest_framework import serializers

from core.custom_serializers import CustomModelSerializer
from review.models import Review


class ReviewSerializer(CustomModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = "user", "is_active"
