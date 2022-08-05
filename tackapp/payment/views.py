from decimal import Decimal, Context

import djstripe.models
import stripe
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from djstripe import webhooks

from djstripe.models import PaymentIntent, Customer
from djmoney.money import Money
from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.decorators import api_view
from rest_framework.response import Response

from payment.serializers import AddBalanceSerializer, MoneyWithdrawalSerializer, BankAccountSerializer, PISerializer
from user.serializers import UserSerializer


class AddBalance(views.APIView):
    """Endpoint for money refill"""

    @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)

        serializer = AddBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer, created = Customer.get_or_create(subscriber=request.user)

        # pi = stripe.PaymentIntent.create(
        #     customer=customer.id,
        #     currency="USD",
        #     amount=serializer.validated_data['balance'],
        #     # receipt_email=customer.email
        # )
        ch = customer.charge(
            amount=Decimal(serializer.validated_data['balance'] / 100, Context(prec=2)),
            currency="USD",
            # application_fee=int(serializer.validated_data['balance'] / 10)
        )
        # ch = stripe.Charge.create(
        #     customer=customer.id,
        #     currency="USD",
        #     amount=serializer.validated_data['balance'],
        #     # receipt_email=customer.email
        # )
        print(ch)
        # customer.balance += ch['amount']
        # customer.save()

        return Response({str(ch)})


class AccountBalanceAdd(views.APIView):
    @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)

        customer, created = Customer.get_or_create(subscriber=request.user)

        serializer = AddBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response()


class AddCreditCard(views.APIView):
    def post(self, request, *args, **kwargs):

        si = stripe.SetupIntent.create(
            stripe_account=Customer.get_or_create(subscriber=request.user)[0].id
        )
        # customer.add_payment_method() ? customer.add_card() ?
        return Response(si)


class MoneyWithdrawal(views.APIView):
    """Endpoint for money withdrawal"""

    @extend_schema(request=MoneyWithdrawalSerializer, responses=MoneyWithdrawalSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)

        serializer = MoneyWithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if Decimal(serializer.data["balance"]) > request.user.bankaccount.usd_balance:
            return Response({"error": "Not enough money"})
        request.user.bankaccount.usd_balance -= Decimal(serializer.data["balance"])
        request.user.bankaccount.save()

        return Response(BankAccountSerializer(request.user.bankaccount).data)
