import json
import logging
from decimal import Decimal, Context

import djstripe.models
import stripe
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from djstripe import webhooks

from djstripe.models import Customer as dsCustomer
from djstripe.models import PaymentMethod as dsPaymentMethod
from djmoney.money import Money
from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.decorators import api_view
from rest_framework.response import Response

from payment.dwolla import dwolla_client
from payment.models import BankAccount
from payment.serializers import AddBalanceSerializer, MoneyWithdrawalSerializer, BankAccountSerializer, PISerializer, \
    AddAccountSerializer, PayoutSerializer, PaymentMethodSerializer, AddWithdrawMethodSerializer
from payment.services import get_dwolla_payment_methods, get_dwolla_id, get_link_token, get_access_token, \
    get_accounts_with_processor_tokens, attach_all_accounts_to_dwolla
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


# class AccountBalanceAdd(views.APIView):
#     @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
#     def post(self, request):
#         if not request.user.is_authenticated:
#             return Response({"message": "User not logged in"}, status=400)
#
#         ds_customer, created = dsCustomer.get_or_create(subscriber=request.user)
#
#         serializer = AddBalanceSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         return Response()


class AddPaymentMethod(views.APIView):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        ds_customer, created = dsCustomer.get_or_create(subscriber=request.user)

        si = stripe.SetupIntent.create(
            customer=ds_customer.id
        )
        return Response(si)


class GetUserPaymentMethods(views.APIView):
    # TODO: add Dwolla API call
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        ds_customer, created = djstripe.models.Customer.get_or_create(
            subscriber=request.user
        )
        pms = dsPaymentMethod.objects.filter(customer=ds_customer)
        serializer = PaymentMethodSerializer(pms, many=True)
        return Response(serializer.data)


class GetUserWithdrawMethods(views.APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        try:
            ba = BankAccount.objects.get(user=request.user)
        except ObjectDoesNotExist:
            # TODO: create dwolla account and return empty list
            return Response({"error": "can not find dwolla user"})

        pms = get_dwolla_payment_methods(ba.dwolla_user)
        return Response(pms)


class GetLinkToken(views.APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        dwolla_id = get_dwolla_id(request.user)
        link_token = get_link_token(dwolla_id)
        logging.getLogger().warning(link_token)
        return Response({"link_token": link_token})


class AddUserWithdrawMethod(views.APIView):

    @extend_schema(request=AddWithdrawMethodSerializer, responses=AddWithdrawMethodSerializer)
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        serializer = AddWithdrawMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access_token = get_access_token(serializer.validated_data['public_token'])
        accounts = get_accounts_with_processor_tokens(access_token)
        attach_all_accounts_to_dwolla(request.user, accounts)
        account_names = [account["official_name"] for account in accounts]
        return Response(account_names)

# class MoneyWithdrawal(views.APIView):
#     """Endpoint for money withdrawal"""
#
#     @extend_schema(request=MoneyWithdrawalSerializer, responses=MoneyWithdrawalSerializer)
#     def post(self, request):
#         if not request.user.is_authenticated:
#             return Response({"message": "User not logged in"}, status=400)
#
#         serializer = MoneyWithdrawalSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         if Decimal(serializer.data["balance"]) > request.user.bankaccount.usd_balance:
#             return Response({"error": "Not enough money"})
#         request.user.bankaccount.usd_balance -= Decimal(serializer.data["balance"])
#         request.user.bankaccount.save()
#
#         return Response(BankAccountSerializer(request.user.bankaccount).data)

