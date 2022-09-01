import json
import logging
from decimal import Decimal, Context

from rest_framework.permissions import IsAuthenticated

import djstripe.models
import dwollav2
import plaid
import stripe
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from core.choices import PaymentType
from djstripe import webhooks

from djstripe.models import Customer as dsCustomer
from djstripe.models import PaymentMethod as dsPaymentMethod
from djmoney.money import Money
from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.decorators import api_view
from rest_framework.response import Response

from dwolla_service.models import DwollaEvent
from payment.models import BankAccount, UserPaymentMethods
from payment.serializers import AddBalanceSerializer, BankAccountSerializer, PISerializer, \
    StripePaymentMethodSerializer, AddWithdrawMethodSerializer, DwollaMoneyWithdrawSerializer, \
    DwollaPaymentMethodSerializer, GetCardByIdSerializer, SetupIntentSerializer, DeletePaymentMethodSerializer, \
    SetPrimaryPaymentMethodSerializer
from payment.services import get_dwolla_payment_methods, get_dwolla_id, get_link_token, get_access_token, \
    get_accounts_with_processor_tokens, attach_all_accounts_to_dwolla, save_dwolla_access_token, check_dwolla_balance, \
    get_dwolla_pms_by_id, dwolla_webhook_handler, dwolla_transaction, detach_dwolla_funding_source, set_primary_method, \
    detach_payment_method


class AddBalanceStripe(views.APIView):
    """Endpoint for money refill from Stripe"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
    def post(self, request):

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

    permission_classes = (IsAuthenticated,)

    @extend_schema(request=AddBalanceSerializer, responses=AddBalanceSerializer)
    def post(self, request):
        serializer = AddBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        payment_method = serializer.validated_data["payment_method"]

        is_enough_funds = check_dwolla_balance(request.user, amount, payment_method)
        if not is_enough_funds:
            return Response({"error": "code", "message": "Insufficient funds"}, status=400)
        try:
            response_body = dwolla_transaction(user=request.user, action="refill", **serializer.validated_data)
        except dwollav2.Error as e:
            return Response(e.body)

        return Response(response_body)


class AddPaymentMethod(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses=None)
    def post(self, request, *args, **kwargs):
        ds_customer, created = dsCustomer.get_or_create(subscriber=request.user)

        si = stripe.SetupIntent.create(
            customer=ds_customer.id
        )
        # serializer = SetupIntentSerializer(si, many=False)
        return Response(si)


class GetUserPaymentMethods(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses=StripePaymentMethodSerializer)
    def get(self, request, *args, **kwargs):
        ds_customer, created = djstripe.models.Customer.get_or_create(
            subscriber=request.user
        )
        pms = dsPaymentMethod.objects.filter(customer=ds_customer)
        serializer = StripePaymentMethodSerializer(pms, many=True)
        return Response({"results": serializer.data})


class GetUserWithdrawMethods(views.APIView):
    """Endpoint for getting Dwolla withdraw methods"""

    permission_classes = (IsAuthenticated,)

    # TODO: get methods from DB
    @extend_schema(request=None, responses=DwollaPaymentMethodSerializer)
    def get(self, request, *args, **kwargs):
        try:
            ba = BankAccount.objects.get(user=request.user)
        except BankAccount.DoesNotExist:
            # TODO: create dwolla account and return empty list
            return Response({"error": "code", "message": "Can not find DB user"}, status=400)

        try:
            pms = get_dwolla_payment_methods(ba.dwolla_user)
        except dwollav2.Error as e:
            return Response(e.body)

        data: list = pms["_embedded"]["funding-sources"]

        dwolla_pm_ids = [funding_source["id"] for funding_source in data]
        upms_values = UserPaymentMethods.objects.filter(
            dwolla_payment_method__in=dwolla_pm_ids
        ).values(
            "dwolla_payment_method",
            "is_primary"
        )

        # TODO: too ugly will change later (31.08.2022)
        for upm in upms_values:
            for funding_source in data:
                if funding_source["id"] == upm["dwolla_payment_method"]:
                    funding_source["is_primary"] = upm["is_primary"]

        serializer = DwollaPaymentMethodSerializer(data, many=True)
        return Response({"results": serializer.data})


class GetLinkToken(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        dwolla_id = get_dwolla_id(request.user)
        link_token = get_link_token(dwolla_id)
        return Response({"link_token": link_token})


class AddUserWithdrawMethod(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=AddWithdrawMethodSerializer, responses=DwollaPaymentMethodSerializer)
    def post(self, request, *args, **kwargs):
        serializer = AddWithdrawMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        public_token = serializer.validated_data['public_token']

        access_token = get_access_token(public_token)
        save_dwolla_access_token(access_token, request.user)
        accounts = get_accounts_with_processor_tokens(access_token)
        try:
            payment_methods = attach_all_accounts_to_dwolla(request.user, accounts)
        except dwollav2.Error as e:
            return Response(e.body, status=e.status)
        except plaid.ApiException as e:
            return Response(e.body, status=e.status)

        try:
            ba = BankAccount.objects.get(user=request.user)
        except BankAccount.DoesNotExist:
            # TODO: create dwolla account and return empty list
            return Response({"error": "code", "message": "Can not find DB user"}, status=400)
        pms = get_dwolla_payment_methods(ba.dwolla_user)
        # pms = get_dwolla_pms_by_id(payment_methods)
        data: list = pms["_embedded"]["funding-sources"]
        dwolla_pm_ids = [funding_source["id"] for funding_source in data]

        upms_values = UserPaymentMethods.objects.filter(
            dwolla_payment_method__in=dwolla_pm_ids
        ).values(
            "dwolla_payment_method",
            "is_primary"
        )

        # TODO: too ugly will change later (31.08.2022)
        for upm in upms_values:
            for funding_source in data:
                if funding_source["id"] == upm["dwolla_payment_method"]:
                    funding_source["is_primary"] = upm["is_primary"]

        serializer = DwollaPaymentMethodSerializer(data, many=True)
        return Response({"results": serializer.data})


class DwollaMoneyWithdraw(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=DwollaMoneyWithdrawSerializer, responses=DwollaMoneyWithdrawSerializer)
    def post(self, request, *args, **kwargs):
        serializer = DwollaMoneyWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ba = BankAccount.objects.get(user=request.user)
            if ba.usd_balance <= serializer.validated_data["amount"]:
                return Response({"error": "code", "message": "Not enough money"}, status=400)
        except BankAccount.DoesNotExist:
            pass
        response_body = dwolla_transaction(user=request.user, action="withdraw", **serializer.validated_data)
        return Response(response_body)


class GetPaymentMethodById(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=GetCardByIdSerializer, responses=StripePaymentMethodSerializer)
    def post(self, request, *args, **kwargs):
        serializer = GetCardByIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment_method_id = serializer["pm_id"]
        ds_customer, created = djstripe.models.Customer.get_or_create(
            subscriber=request.user
        )
        try:
            pm = dsPaymentMethod.objects.get(id=payment_method_id, customer=ds_customer.id)
        except dsPaymentMethod.DoesNotExist:
            return Response(
                {
                    "error": "code",
                    "message": "Payment method not found"
                },
                status=400
            )

        return Response(StripePaymentMethodSerializer(pm))


class DetachPaymentMethod(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=DeletePaymentMethodSerializer, responses=DeletePaymentMethodSerializer)
    def post(self, request, *args, **kwargs):
        serializer = DeletePaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            detach_payment_method(
                user=request.user,
                payment_type=serializer.validated_data["payment_type"],
                payment_method=serializer.validated_data["payment_method"]
            )
        except dwollav2.Error as e:
            return Response(e.body, status=e.status)
        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "code",
                    "message": "Payment method doesn't exist"
                },
                status=400
            )
        return Response(
            {
                "error": None,
                "message": "Successfully detached",
                "payment_method": serializer.data["payment_method"]
            }
        )


class SetPrimaryPaymentMethod(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=SetPrimaryPaymentMethodSerializer, responses=SetPrimaryPaymentMethodSerializer)
    def post(self, request, *args, **kwargs):
        serializer = SetPrimaryPaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            set_primary_method(
                user=request.user,
                payment_type=serializer.validated_data["payment_type"],
                payment_method=serializer.validated_data["payment_method"]
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "code",
                    "message": "Payment method does not exist",
                    "payment_method": serializer.validated_data["payment_method"]
                })
        return Response(
            {
                "error": None,
                "message": "Successfully updated primary method",
                "payment_method": serializer.validated_data["payment_method"]
            }
        )


class DwollaWebhook(views.APIView):
    def post(self, request, *args, **kwargs):
        dwolla_webhook_handler(request)
        # logging.getLogger().warning(f"{request.data = }")
        return Response()
