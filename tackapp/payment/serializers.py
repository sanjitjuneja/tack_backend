from rest_framework import serializers
from djmoney.contrib.django_rest_framework import MoneyField

from core.validators import supported_currency
from payment.models import BankAccount


class AddBalanceSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=1, max_value=10_000, default=10)
    balance_currency = serializers.CharField(default="USD", validators=(supported_currency,))


class MoneyWithdrawalSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=1, max_value=10_000, default=10)
    balance_currency = serializers.CharField(default="USD", validators=(supported_currency,))
    # card?


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "__all__"
