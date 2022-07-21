from rest_framework import serializers
from user.serializers import UserListSerializer
from .models import *


class TackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tack
        fields = (
            "id",
            "tacker",
            "runner",
            "title",
            "price",
            "status",
            "expiration_time",
            "estimation_time_seconds",
        )
        read_only_fields = (
            "id",
            "tacker",
            "runner",
            "status",
        )


class TackDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tack
        fields = "__all__"
        read_only_fields = (
            "tacker",
            "runner",
            "status",
            "completion_message",
            "completion_time",
        )


class AcceptRunnerSerializer(serializers.Serializer):
    runner_id = serializers.IntegerField(min_value=1)


class TackCompleteSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=256, allow_blank=True, default="")


class AcceptOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = (
            "tack",
            "runner",
            "price",
            "offer_type",
            "is_accepted"
        )


class OfferSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        offer_type = OfferType.counter_offer if validated_data.get("price") else OfferType.offer
        instance = Offer.objects.create(
            **validated_data,
            offer_type=offer_type
        )

        return instance

    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = "runner", "is_accepted", "offer_type"


class TackUserSerializer(serializers.ModelSerializer):
    tacker = UserListSerializer(read_only=True)

    class Meta:
        model = Tack
        fields = (
            "id",
            "tacker",
            "runner",
            "title",
            "price",
            "status",
            "estimation_time_seconds",
        )
        read_only_fields = (
            "id",
            "tacker",
            "runner",
            "status",
        )