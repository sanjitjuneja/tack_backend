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

from payment.serializers import AddBalanceSerializer, MoneyWithdrawalSerializer, BankAccountSerializer, PISerializer, \
    AddAccountSerializer, PayoutSerializer
from user.serializers import UserSerializer


class AddBalance(views.APIView):
    """Endpoint for money refill"""

    @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)

        serializer = AddBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # customer, created = Customer.get_or_create(subscriber=request.user)

        # pi = stripe.PaymentIntent.create(
        #     customer=customer.id,
        #     currency="USD",
        #     amount=serializer.validated_data['balance'],
        #     # receipt_email=customer.email
        # )
        # ch = customer.charge(
        #     amount=Decimal(serializer.validated_data['balance'] / 100, Context(prec=2)),
        #     currency="USD",
        #     # application_fee=int(serializer.validated_data['balance'] / 10)
        # )
        # ch = stripe.Charge.create(
        #     customer=customer.id,
        #     currency="USD",
        #     amount=serializer.validated_data['balance'],
        #     # receipt_email=customer.email
        # )
        # print(ch)
        # customer.balance += ch['amount']
        # customer.save()\
        # account = stripe.Account.create(
        #     type="express"
        # )
        # balance = stripe.Balance.retrieve()
        # print(balance)
        payout = stripe.Payout.create(
            amount=990,
            currency='usd',
            # method='instant',
            destination='acct_1LUnhFQkadbscSaM',
        )
        # account = stripe.Account.create(
        #     country="US",
        #     type="custom",
        #     business_type="individual",
        #     email="exmaple2@test.com",
        #     capabilities={
        #         "card_payments": {"requested": True},
        #         "transfers": {"requested": True},
        #     },
        #     individual={
        #         "email": "exmaple2@test.com",
        #         "first_name": "test",
        #         "last_name": "lastnametest",
        #         # "phone": "+375291111111"
        #     }
        # )
        return Response(payout)


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
            stripe_account="acct_1KYDDWHUDqRuKWfq"
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


class AddAccount(views.APIView):

    @extend_schema(request=AddAccountSerializer, responses=AddAccountSerializer)
    def post(self, request, *args, **kwargs):
        serializer = AddAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = stripe.Account.create(
            country=serializer.validated_data["country"],
            email=serializer.validated_data["email"],
            type=serializer.validated_data["type"],
            business_type=serializer.validated_data["business_type"],
            capabilities={
                "card_payments": {"requested": serializer.validated_data["capabilities"]["card_payments"]},
                "transfers": {"requested": serializer.validated_data["capabilities"]["transfers"]},
            },
        )
        return Response(account)


class PayoutView(views.APIView):

    @extend_schema(request=PayoutSerializer, responses=PayoutSerializer)
    def post(self, request, *args, **kwargs):
        serializer = PayoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payout = stripe.Payout.create(
            amount=serializer.validated_data["amount"],
            currency=serializer.validated_data["currency"],
            destination=serializer.validated_data["destination"],
            method=serializer.validated_data["method"]
        )
        return Response(payout)


# class DwollaTest(views.APIView):
#
#     def post(self, request, *args, **kwargs):
#         dwo
#         return Response({"ok"})
