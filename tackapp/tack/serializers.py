from rest_framework import serializers
from core.choices import OfferType
from core.custom_serializers import CustomModelSerializer, CustomSerializer
from group.serializers import GroupSerializer
from user.serializers import UserSerializer, UserListSerializer
from .models import *
from phonenumber_field.serializerfields import PhoneNumberField


class TackSerializer(CustomModelSerializer):
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


class TackDetailSerializer(CustomModelSerializer):
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
            "group",
            "accepted_time",
        )


class TackCreateSerializer(CustomModelSerializer):
    class Meta:
        model = Tack
        fields = (
            "title",
            "type",
            "group",
            "price",
            "description",
            "allow_counter_offer",
            "estimation_time_seconds"
        )


class TackRunnerSerializer(CustomModelSerializer):
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


class AcceptRunnerSerializer(CustomSerializer):
    runner_id = serializers.IntegerField(min_value=1)


class TackCompleteSerializer(CustomSerializer):
    message = serializers.CharField(max_length=256, allow_blank=True, default="")
    # tack = serializers.RelatedField(read_only=True, source="tack.Tack")

    # def to_representation(self, obj):
    #     ret = super(TackCompleteSerializer, self).to_representation(obj)
    #     print(f"{ret = }")
    #     ret.pop('message')
    #     return ret


class AcceptOfferSerializer(CustomModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = (
            "tack",
            "runner",
            "price",
            "offer_type",
            "is_accepted",
            "lifetime_seconds",
            "is_active",
            "status"
        )


class OfferSerializer(CustomModelSerializer):
    def create(self, validated_data):
        offer_type = OfferType.COUNTER_OFFER if validated_data.get("price") else OfferType.OFFER
        instance = Offer.objects.create(
            **validated_data,
            offer_type=offer_type
        )

        return instance

    runner = UserListSerializer(read_only=True)

    class Meta:
        model = Offer
        fields = "__all__"
        read_only_fields = (
            "runner", "is_accepted", "offer_type", "creation_time", "lifetime_seconds", "is_active", "status"
        )


class TackUserSerializer(CustomModelSerializer):
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


class TacksOffersSerializer(CustomSerializer):
    id = serializers.SerializerMethodField()
    tack = TackDetailSerializer()
    offer = serializers.SerializerMethodField()

    def get_offer(self, obj: Offer) -> OfferSerializer:
        return OfferSerializer(obj).data

    def get_id(self, obj: Offer) -> int:
        return obj.id


class PopularTackSerializer(CustomModelSerializer):
    class Meta:
        model = PopularTack
        fields = ("title", "description", "type", "price", "allow_counter_offer", "estimation_time_seconds")


class TackTemplateSerializer(CustomModelSerializer):
    class Meta:
        model = Tack
        fields = ("title", "description", "type", "price", "allow_counter_offer", "estimation_time_seconds")


class ContactsSerializer(CustomModelSerializer):
    class Meta:
        model = User
        fields = "phone_number", "email"
        read_only_fields = "phone_number", "email"


class GroupTackSerializer(CustomSerializer):
    id = serializers.SerializerMethodField()
    tack = serializers.SerializerMethodField()
    is_mine_offer_sent = serializers.SerializerMethodField()

    def get_id(self, obj) -> int:
        return obj.id

    def get_tack(self, obj: Tack) -> TackDetailSerializer:
        return TackDetailSerializer(obj, many=False).data

    def get_is_mine_offer_sent(self, obj) -> bool:
        return obj.offer_set.all().exists()
