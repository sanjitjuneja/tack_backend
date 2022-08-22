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

from payment.models import BankAccount
from payment.serializers import AddBalanceSerializer, BankAccountSerializer, PISerializer, \
    StripePaymentMethodSerializer, AddWithdrawMethodSerializer, DwollaMoneyWithdrawSerializer, DwollaPaymentMethodSerializer
from payment.services import get_dwolla_payment_methods, get_dwolla_id, get_link_token, get_access_token, \
    get_accounts_with_processor_tokens, attach_all_accounts_to_dwolla, save_dwolla_access_token, check_dwolla_balance, \
    withdraw_dwolla_money, refill_dwolla_money
from user.serializers import UserSerializer


class AddBalanceStripe(views.APIView):
    """Endpoint for money refill from Stripe"""

    @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)

        serializer = AddBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer, created = dsCustomer.get_or_create(subscriber=request.user)

        pi = stripe.PaymentIntent.create(
            customer=customer.id,
            receipt_email=customer.email,
            **serializer.validated_data
        )

        return Response(pi)


class AddBalanceDwolla(views.APIView):
    """Endpoint for money refill from Dwolla"""

    @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)

        serializer = AddBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        payment_method = serializer.validated_data["payment_method"] \
            if serializer.validated_data.get("payment_method") \
            else None

        check_dwolla_balance(request.user, amount, payment_method)
        response_body = refill_dwolla_money(request.user, **serializer.validated_data)
        return Response(response_body)


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
        serializer = StripePaymentMethodSerializer(pms, many=True)
        return Response(serializer.data)


class GetUserWithdrawMethods(views.APIView):
    """Endpoint for getting Dwolla withdraw methods"""

    # TODO: get methods from DB
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        try:
            ba = BankAccount.objects.get(user=request.user)
        except ObjectDoesNotExist:
            # TODO: create dwolla account and return empty list
            return Response({"error": "can not find dwolla user"})

        pms = get_dwolla_payment_methods(ba.dwolla_user)
        data = pms["_embedded"]["funding-sources"]
        logging.getLogger().warning(data)
        serializer = DwollaPaymentMethodSerializer(data, many=True)
        return Response(serializer.data)


class GetLinkToken(views.APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        dwolla_id = get_dwolla_id(request.user)
        link_token = get_link_token(dwolla_id)
        return Response({"link_token": link_token})


class AddUserWithdrawMethod(views.APIView):
    @extend_schema(request=AddWithdrawMethodSerializer, responses=AddWithdrawMethodSerializer)
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        serializer = AddWithdrawMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        public_token = serializer.validated_data['public_token']

        # TODO: attach access to current User
        access_token = get_access_token(public_token)
        save_dwolla_access_token(access_token, request.user)
        accounts = get_accounts_with_processor_tokens(access_token)
        account_names = attach_all_accounts_to_dwolla(request.user, accounts)

        return Response(account_names)


class DwollaMoneyWithdraw(views.APIView):
    @extend_schema(request=DwollaMoneyWithdrawSerializer, responses=DwollaMoneyWithdrawSerializer)
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"message": "User not logged in"}, status=400)
        serializer = DwollaMoneyWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ba = BankAccount.objects.get(user=request.user)
            if ba.usd_balance <= serializer.validated_data["amount"]:
                return Response({"error": "Not enough money"})
        except BankAccount.DoesNotExist:
            pass
        response_body = withdraw_dwolla_money(request.user, **serializer.validated_data)
        return Response(response_body)


class DwollaWebhook(views.APIView):
    def post(self, request, *args, **kwargs):
        logging.getLogger().warning(request)
        return Response()
