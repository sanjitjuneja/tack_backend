from rest_framework import serializers
from core.choices import OfferType
from group.serializers import GroupSerializer
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
            "estimation_time_seconds",
        )
        read_only_fields = (
            "id",
            "tacker",
            "runner",
            "status",
        )


class TackDetailSerializer(serializers.ModelSerializer):
    tacker = UserListSerializer(read_only=True)
    runner = UserListSerializer(read_only=True)
    group = GroupSerializer(read_only=True)

    class Meta:
        model = Tack
        fields = "__all__"
        read_only_fields = (
            "tacker",
            "runner",
            "status",
            "completion_message",
            "completion_time",
            "is_paid",
            "group"
        )


class TackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tack
        fields = "__all__"
        read_only_fields = (
            "tacker",
            "runner",
            "status",
            "completion_message",
            "completion_time",
            "is_paid",
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
            "is_accepted",
            "lifetime_seconds"
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

    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = (
            "runner", "is_accepted", "offer_type", "creation_time", "lifetime_seconds"
        )


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


class TacksOffersSerializer(serializers.Serializer):
    tack = TackDetailSerializer()
    offer = serializers.SerializerMethodField()

    def get_offer(self, obj: Offer):
        return OfferSerializer(obj).data


# class TacksOffersSerializer2(serializers.ModelSerializer):
#     tack = TackDetailSerializer()
#     offer = OfferSerializer()
#
#     class Meta:
#         model = TacksOffers
#         fields = "__all__"

