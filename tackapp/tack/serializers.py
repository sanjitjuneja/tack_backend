import logging

from rest_framework import serializers

from core.choices import MethodType
from core.custom_serializers import CustomModelSerializer, CustomSerializer
from group.serializers import GroupSerializer
from user.serializers import UserListSerializer
from .models import *


logger = logging.getLogger('debug')


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
            "auto_accept",
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

    # def validate(self, attrs):
    #     logger.debug(f"{attrs = }")
    #     return attrs

    def to_internal_value(self, data):
        logger.debug(f"{data = }")
        logger.debug(f"{self.fields = }")
        if data.get("auto_accept"):
            data["allow_counter_offer"] = False

        logger.debug(f"{data = }")
        return super().to_internal_value(data)

    class Meta:
        model = Tack
        fields = (
            "title",
            "type",
            "group",
            "price",
            "description",
            "allow_counter_offer",
            "estimation_time_seconds",
            "auto_accept",
        )


class PaymentInfoSerializer(serializers.Serializer):
    transaction_id = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    method_type = serializers.ChoiceField(choices=MethodType.choices, required=True)


class TackCreateSerializerv2(CustomSerializer):
    payment_info = PaymentInfoSerializer(required=True)
    tack = TackCreateSerializer(required=True)

    def __init__(self, *args, **kwargs):
        """
        Added for reverse compatibility with TackCreateSerializer from older builds
        If there is no 'tack' entity inside JSON structure -
        we form our V2 Serializer based on TackCreateSerializer fields
        Also we add payment_info["method_type"] field default to MethodType.TACK_BALANCE
        """

        tack = kwargs['data'].get('tack', None)
        if tack:
            super().__init__(*args, **kwargs)
        else:
            tack_data = {}
            for key in kwargs['data']:
                tack_data[key] = kwargs['data'].get(key)
            kwargs = {'data': {}}
            kwargs['data']["payment_info"] = {}
            kwargs['data']["tack"] = tack_data
            kwargs['data']["payment_info"]["method_type"] = MethodType.TACK_BALANCE.value
            super().__init__(*args, **kwargs)

    def create(self, validated_data):
        logger.debug(f"{validated_data = }")
        tack_validated_data = validated_data.pop("tack")
        return Tack.objects.create(**tack_validated_data, tacker=validated_data.get("tacker"))


class TackRunnerSerializer(CustomModelSerializer):
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


class AcceptOfferSerializer(CustomModelSerializer):
    def __init__(self, *args, **kwargs):
        """
        Added for reverse compatibility with old AcceptOfferSerializer
        If there is no 'payment_info' entity inside JSON structure -
        We add payment_info["method_type"] field default to MethodType.TACK_BALANCE
        """

        payment_info = kwargs['data'].get('payment_info', None)
        if payment_info:
            super().__init__(*args, **kwargs)
        else:
            kwargs = {'data': {}}
            kwargs['data']["payment_info"] = {"method_type": MethodType.TACK_BALANCE.value}
            super().__init__(*args, **kwargs)

    payment_info = PaymentInfoSerializer(required=False)

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
        fields = (
            "title",
            "description",
            "type",
            "price",
            "allow_counter_offer",
            "estimation_time_seconds",
            "auto_accept",
        )


class TackTemplateSerializer(CustomModelSerializer):
    class Meta:
        model = Tack
        fields = (
            "title",
            "description",
            "type",
            "price",
            "allow_counter_offer",
            "estimation_time_seconds",
            "auto_accept",
        )


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
