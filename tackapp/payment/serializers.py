import djstripe.models
from rest_framework import serializers
from djmoney.contrib.django_rest_framework import MoneyField
from djstripe.models.payment_methods import PaymentMethod as dsPaymentMethod

from core.validators import supported_currency
from payment.models import BankAccount


class AddBalanceSerializer(serializers.Serializer):
    balance = serializers.IntegerField(min_value=100, max_value=10_000_00)
    balance_currency = serializers.CharField(default="USD", validators=(supported_currency,))


class MoneyWithdrawalSerializer(serializers.Serializer):
    balance = serializers.IntegerField(min_value=100, max_value=10_000_00)
    balance_currency = serializers.CharField(default="USD", validators=(supported_currency,))
    # card?


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "usd_balance", "user"
        read_only_fields = "usd_balance", "user"


class PISerializer(serializers.ModelSerializer):
    class Meta:
        model = djstripe.models.PaymentIntent
        fields = "__all__"


class CapabilitiesSerializer(serializers.Serializer):
    card_payments = serializers.BooleanField(default=True)
    transfers = serializers.BooleanField(default=True)


class AddAccountSerializer(serializers.Serializer):
    country = serializers.CharField(max_length=64, default="US")
    type = serializers.CharField(max_length=64, default="custom")
    business_type = serializers.CharField(max_length=64, default="individual")
    email = serializers.CharField(max_length=64, default="exmaple2@test.com")
    capabilities = CapabilitiesSerializer()


class PayoutSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, default=1000)
    currency = serializers.CharField(min_length=1, default="USD")
    method = serializers.CharField(min_length=1, default="instant"),
    destination = serializers.CharField(min_length=1, default='acct_1KYDDWHUDqRuKWfq')


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
