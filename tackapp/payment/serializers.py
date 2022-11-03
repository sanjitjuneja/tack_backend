import logging

from django.db import transaction
from rest_framework.exceptions import ValidationError

import djstripe.models
import stripe
from rest_framework import serializers
from djstripe.models.payment_methods import PaymentMethod as dsPaymentMethod

from core.choices import images_dict, PaymentType, MethodType
from core.validators import supported_currency
from payment.models import BankAccount, StripePaymentMethodsHolder, Fee, Transfer


logger = logging.getLogger('debug')


class AddBalanceStripeSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1_00, max_value=4_000_00)
    currency = serializers.CharField(default="USD", validators=(supported_currency,))
    payment_method = serializers.CharField(min_length=6, required=False, allow_null=True)


class AddBalanceDwollaSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1_00, max_value=4_000_00)
    currency = serializers.CharField(default="USD", validators=(supported_currency,))
    payment_method = serializers.CharField(min_length=6, required=False)
    channel = serializers.CharField(required=False)


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "id", "usd_balance"
        read_only_fields = "id", "usd_balance"


class PISerializer(serializers.ModelSerializer):
    class Meta:
        model = djstripe.models.PaymentIntent
        fields = "__all__"


class CapabilitiesSerializer(serializers.Serializer):
    card_payments = serializers.BooleanField(default=True)
    transfers = serializers.BooleanField(default=True)


class AddCreditCardSerializer(serializers.Serializer):
    customer_id = serializers.CharField(max_length=32)


class StripeBillingDetailsSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)


class StripeCardSerializer(serializers.Serializer):
    brand = serializers.CharField(read_only=True)
    last4 = serializers.CharField(read_only=True)
    wallet = serializers.CharField(read_only=True)
    country = serializers.CharField(read_only=True)
    funding = serializers.CharField(read_only=True)
    exp_year = serializers.IntegerField(read_only=True)
    exp_month = serializers.IntegerField(read_only=True)
    image = serializers.SerializerMethodField()

    def get_image(self, obj) -> str:
        image = images_dict[obj["brand"]] if obj.get("brand") in images_dict else None
        return image


class StripePaymentMethodSerializer(serializers.ModelSerializer):
    billing_details = StripeBillingDetailsSerializer(read_only=True)
    card = StripeCardSerializer(read_only=True)
    is_primary = serializers.SerializerMethodField()

    def get_is_primary(self, obj) -> bool:
        stripe_pm_holder = StripePaymentMethodsHolder.objects.get(stripe_pm__id=obj.id)
        return stripe_pm_holder.is_primary

    class Meta:
        model = dsPaymentMethod
        fields = "id", "created", "billing_details", "type", "card", "is_primary"


class AddWithdrawMethodSerializer(serializers.Serializer):
    public_token = serializers.CharField(max_length=256)


class DwollaMoneyWithdrawSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1_00, max_value=4000_00)
    currency = serializers.CharField(default="USD", validators=(supported_currency,))
    payment_method = serializers.CharField(min_length=6)
    channel = serializers.CharField(required=False)


class DwollaPaymentMethodSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    bankAccountType = serializers.CharField(read_only=True)
    created = serializers.CharField(read_only=True)
    channels = serializers.ListField(read_only=True)
    bankName = serializers.CharField(read_only=True)
    image = serializers.SerializerMethodField()
    is_primary = serializers.BooleanField()

    def get_image(self, obj) -> str | None:
        image = images_dict[obj["bankName"]] if obj.get("bankName") in images_dict else None
        return image


class GetCardByIdSerializer(serializers.Serializer):
    pm_id = serializers.CharField(write_only=True)
    payment_method = StripePaymentMethodSerializer(read_only=True)


class SetupIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = stripe.SetupIntent
        fields = "__all__"


class DeletePaymentMethodSerializer(serializers.Serializer):
    payment_type = serializers.ChoiceField(PaymentType.choices)
    payment_method = serializers.CharField()


class SetPrimaryPaymentMethodSerializer(serializers.Serializer):
    payment_type = serializers.ChoiceField(PaymentType.choices)
    payment_method = serializers.CharField()


class FeeSerializer(serializers.Serializer):
    stripe = serializers.SerializerMethodField()
    dwolla = serializers.SerializerMethodField()

    def get_stripe(self, obj: Fee) -> dict:
        return {
            "fee_percent": obj.fee_percent_stripe,
            "fee_min": obj.fee_min_stripe,
            "fee_max": obj.fee_max_stripe
        }

    def get_dwolla(self, obj: Fee) -> dict:
        return {
            "fee_percent": obj.fee_percent_dwolla,
            "fee_min": obj.fee_min_dwolla,
            "fee_max": obj.fee_max_dwolla
        }


class PaymentInfoSerializer(serializers.Serializer):
    transaction_id = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    method_type = serializers.ChoiceField(choices=MethodType.choices, required=True)


class TransferSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        logger.debug(f"inside TransferSerializer validate {attrs = }")
        if attrs['amount'] <= 0:
            raise ValidationError(
                {
                    "amount": "Amount should be more than 0"
                }
            )
        return attrs

    class Meta:
        model = Transfer
        fields = "__all__"
        read_only_fields = ("creation_time", "is_active", "sender", "id", "transaction_id", "method_type")


class TransferCreateSerializer(serializers.Serializer):
    payment_info = PaymentInfoSerializer()
    transfer = TransferSerializer()

    def create(self, validated_data):
        logger.debug(f"{validated_data = }")
        transfer = validated_data.get("transfer")
        payment_info = validated_data.get("payment_info")
        sender = validated_data.get("sender")
        receiver = transfer.get("receiver")
        amount = transfer.get("amount")

        with transaction.atomic():
            db_transfer = Transfer.objects.create(
                sender=sender,
                **transfer,
                **payment_info
            )
            ba_sender = BankAccount.objects.get(user=sender)
            ba_receiver = BankAccount.objects.get(user=receiver)
            ba_sender.usd_balance -= amount
            ba_receiver.usd_balance += amount
            ba_sender.save()
            ba_receiver.save()
        return db_transfer
