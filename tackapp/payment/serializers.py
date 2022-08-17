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


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = dsPaymentMethod
        # fields = "djstripe_id", "id", "billing_details", "type", "card",
        # fields = "__all__"
        exclude = "djstripe_owner_account", "customer"


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
