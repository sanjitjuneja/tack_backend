from rest_framework import serializers
from core.choices import OfferType
from user.serializers import UserSerializer, UserListSerializer
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
    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     for _ in TackStatus.choices:
    #         ret["status"] = _[1] if ret["status"] == _[0] else ret["status"]
    #     return ret
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


class TackRunnerSerializer(serializers.ModelSerializer):
    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     for _ in TackStatus.choices:
    #         ret["status"] = _[1] if ret["status"] == _[0] else ret["status"]
    #     return ret
    tacker = UserListSerializer(read_only=True)

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
    # tack = serializers.RelatedField(read_only=True, source="tack.Tack")

    # def to_representation(self, obj):
    #     ret = super(TackCompleteSerializer, self).to_representation(obj)
    #     print(f"{ret = }")
    #     ret.pop('message')
    #     return ret


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

    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     for _ in OfferType.choices:
    #         ret["offer_type"] = _[1] if ret["offer_type"] == _[0] else ret["offer_type"]
    #     return ret


class OfferSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        offer_type = OfferType.counter_offer if validated_data.get("price") else OfferType.offer
        instance = Offer.objects.create(
            **validated_data,
            offer_type=offer_type
        )

        return instance

    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     for _ in OfferType.choices:
    #         if ret.get("offer_type"):
    #             ret["offer_type"] = _[1] if ret["offer_type"] == _[0] else ret["offer_type"]
    #     return ret

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


# class TacksOffersSerializer(serializers.ModelSerializer):
#     tack = TackUserSerializer(read_only=True)
#
#     class Meta:
#         model = Offer
#         fields = "__all__"
#         read_only_fields = "id", "tack", "runner", "price", "is_accepted", "offer_type"


class TacksOffersSerializer(serializers.Serializer):
    data = serializers.SerializerMethodField()

    def get_data(self, obj: Offer):
        return {
            "offer": {
                "id": obj.id,
                "type": obj.offer_type,
                "price": obj.price,
                "offer_type": obj.offer_type,
                "is_accepted": obj.is_accepted,
                "runner": obj.runner.id,
                "creation_time": obj.creation_time,
                "lifetime_seconds": obj.lifetime_seconds
                },
            "tack": {
                "id": obj.tack.id,
                "tacker": {
                    "id": obj.tack.tacker.id,
                    "first_name": obj.tack.tacker.first_name,
                    "last_name": obj.tack.tacker.last_name,
                    "tacks_rating": obj.tack.tacker.tacks_rating,
                    "tacks_amount": obj.tack.tacker.tacks_amount,
                },
                "title": obj.tack.title,
                "price": obj.tack.price,
                "status": obj.tack.status,
                "estimation_time_seconds": obj.tack.estimation_time_seconds,
                }
            }
