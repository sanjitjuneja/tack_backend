from djmoney.money import Money
from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.response import Response

from payment.serializers import AddBalanceSerializer, MoneyWithdrawalSerializer
from user.serializers import UserSerializer


class AddBalance(views.APIView):
    """Endpoint for money refill"""

    @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)

        serializer = AddBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.balance += Money(serializer.data["balance"], serializer.data["balance_currency"])
        request.user.save()
        return Response(UserSerializer(request.user).data)


class MoneyWithdrawal(views.APIView):
    """Endpoint for money withdrawal"""

    @extend_schema(request=MoneyWithdrawalSerializer, responses=MoneyWithdrawalSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)

        serializer = MoneyWithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if Money(serializer.data["balance"], serializer.data["balance_currency"]) > request.user.balance:
            return Response({"error": "Not enough money"})
        request.user.balance -= Money(serializer.data["balance"], serializer.data["balance_currency"])
        request.user.save()

        return Response(UserSerializer(request.user).data)
