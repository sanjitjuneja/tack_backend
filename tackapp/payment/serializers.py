import djstripe.models
from rest_framework import serializers
from djmoney.contrib.django_rest_framework import MoneyField
from djstripe.models.payment_methods import PaymentMethod as dsPaymentMethod

from core.validators import supported_currency
from payment.models import BankAccount


class AddBalanceSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1_00, max_value=4_000_00)
    currency = serializers.CharField(default="USD", validators=(supported_currency,))
    payment_method = serializers.CharField(min_length=6)


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "usd_balance",
        read_only_fields = "usd_balance",


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


class StripePaymentMethodSerializer(serializers.ModelSerializer):
    billing_details = StripeBillingDetailsSerializer(read_only=True)
    card = StripeCardSerializer(read_only=True)

    class Meta:
        model = dsPaymentMethod
        fields = "id", "created", "billing_details", "type", "card",


class AddWithdrawMethodSerializer(serializers.Serializer):
    public_token = serializers.CharField(max_length=256)


class DwollaMoneyWithdrawSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1_00, max_value=4000_00)
    currency = serializers.CharField(default="USD", validators=(supported_currency,))
    payment_method = serializers.CharField(min_length=6)


class DwollaPaymentMethodSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    bankAccountType = serializers.CharField(read_only=True)
    created = serializers.CharField(read_only=True)
    channels = serializers.ListField(read_only=True)
    bankName = serializers.CharField(read_only=True)


class GetCardByIdSerializer(serializers.Serializer):
    pm_id = serializers.CharField(write_only=True)
    payment_method = StripePaymentMethodSerializer(read_only=True)
