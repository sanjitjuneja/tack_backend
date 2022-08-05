import djstripe.models
from rest_framework import serializers
from djmoney.contrib.django_rest_framework import MoneyField

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
