import logging
from datetime import timedelta

from django.db.models import Sum, Q, F
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated

import djstripe.models
import dwollav2
import plaid
import stripe
from django.core.exceptions import ObjectDoesNotExist

from core.choices import PaymentType, PaymentService, PaymentAction

from djstripe.models import Customer as dsCustomer
from djstripe.models import PaymentMethod as dsPaymentMethod
from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.response import Response

from payment.models import BankAccount, UserPaymentMethods, Transaction, Fee
from payment.serializers import StripePaymentMethodSerializer, AddWithdrawMethodSerializer, \
    DwollaMoneyWithdrawSerializer, DwollaPaymentMethodSerializer, GetCardByIdSerializer, \
    DeletePaymentMethodSerializer, SetPrimaryPaymentMethodSerializer, AddBalanceDwollaSerializer, \
    AddBalanceStripeSerializer, FeeSerializer
from payment.services import get_dwolla_payment_methods, get_dwolla_id, get_link_token, get_access_token, \
    get_accounts_with_processor_tokens, attach_all_accounts_to_dwolla, save_dwolla_access_token, check_dwolla_balance, \
    get_dwolla_pms_by_id, dwolla_webhook_handler, dwolla_transaction, detach_dwolla_funding_source, set_primary_method, \
    detach_payment_method, update_dwolla_pms_with_primary, calculate_amount_with_fees, get_sum24h_transactions, \
    calculate_transaction_loss


class AddBalanceStripe(views.APIView):
    """Endpoint for money refill from Stripe"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(request=AddBalanceStripeSerializer, responses=AddBalanceStripeSerializer)
    def post(self, request):

        serializer = AddBalanceStripeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logger = logging.getLogger()

        customer, created = dsCustomer.get_or_create(subscriber=request.user)

        # Calculate new amount because we charge fees
        amount_with_fees = calculate_amount_with_fees(
            serializer.validated_data["amount"],
            service=PaymentService.STRIPE
        )

        sum24h = get_sum24h_transactions(user=request.user)
        current_transaction_loss = calculate_transaction_loss(
            amount=serializer.validated_data["amount"],
            service=PaymentService.STRIPE
        )

        logging.getLogger().warning(f"{current_transaction_loss = }")
        total_loss = sum24h + current_transaction_loss
        if total_loss >= Fee.objects.all().last().max_loss:
            return Response(
                {
                    "error": "code",
                    "message": "You reached your 24h transaction limit"
                },
                status=400)

        # TODO: try-except block
        pi = stripe.PaymentIntent.create(
            customer=customer.id,
            receipt_email=customer.email,
            amount=amount_with_fees,
            currency=serializer.validated_data["currency"],
            payment_method=serializer.validated_data["payment_method"]
        )
        Transaction.objects.create(
            user=request.user,
            is_stripe=True,
            amount_requested=serializer.validated_data["amount"],
            amount_with_fees=amount_with_fees,
            transaction_id=pi["id"]
        )
        logger.warning(f"{pi = }")
        logger.warning(f"{type(pi) = }")
        return Response(pi)


class AddBalanceDwolla(views.APIView):
    """Endpoint for money deposit from Dwolla"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(request=AddBalanceDwollaSerializer, responses=AddBalanceDwollaSerializer)
    def post(self, request):
        serializer = AddBalanceDwollaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        payment_method = serializer.validated_data["payment_method"]

        sum24h = get_sum24h_transactions(user=request.user)
        current_transaction_loss = calculate_transaction_loss(
            amount=serializer.validated_data["amount"],
            service=PaymentService.DWOLLA
        )
        logging.getLogger().warning(f"{current_transaction_loss = }")
        total_loss = sum24h + current_transaction_loss
        if total_loss >= Fee.objects.all().last().max_loss:
            return Response(
                {
                    "error": "code",
                    "message": "You reached your 24h transaction limit"
                },
                status=400)

        is_enough_funds = check_dwolla_balance(request.user, amount, payment_method)
        if not is_enough_funds:
            return Response({"error": "code", "message": "Insufficient funds"}, status=400)
        try:
            response_body = dwolla_transaction(
                user=request.user,
                action=PaymentAction.DEPOSIT,
                **serializer.validated_data
            )
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
        return Response(si)


class GetUserPaymentMethods(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses=StripePaymentMethodSerializer)
    def get(self, request, *args, **kwargs):
        ds_customer, created = djstripe.models.Customer.get_or_create(
            subscriber=request.user
        )
        logging.getLogger().warning(f"{ds_customer = }")
        pms = dsPaymentMethod.objects.filter(customer=ds_customer)
        logging.getLogger().warning(f"{pms = }")
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
            return Response(
                {
                    "error": "code",
                    "message": "Can not find DB user"
                },
                status=400)

        try:
            pms = get_dwolla_payment_methods(ba.dwolla_user)
        except dwollav2.Error as e:
            return Response(e.body)

        data = update_dwolla_pms_with_primary(pms, request.user)
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
            ba = BankAccount.objects.get(user=request.user)
        except BankAccount.DoesNotExist:
            # TODO: create dwolla account and return empty list
            return Response(
                {
                    "error": "code",
                    "message": "Can not find DB user"
                },
                status=400)

        adding_first_bank = False if UserPaymentMethods.objects.filter(bank_account=ba).exists() else True

        try:
            attach_all_accounts_to_dwolla(request.user, accounts)
        except dwollav2.Error as e:
            return Response(e.body, status=e.status)
        except plaid.ApiException as e:
            return Response(e.body, status=e.status)

        pms = get_dwolla_payment_methods(ba.dwolla_user)
        data = update_dwolla_pms_with_primary(pms, request.user)
        if adding_first_bank:
            set_primary_method(
                user=request.user,
                payment_type=PaymentType.BANK,
                payment_method=data[0]["id"]
            )
            data[0]["is_primary"] = True
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

        sum24h = get_sum24h_transactions(user=request.user)
        current_transaction_loss = calculate_transaction_loss(
            amount=serializer.validated_data["amount"],
            service=PaymentService.DWOLLA
        )
        total_loss = sum24h + current_transaction_loss
        if total_loss >= Fee.objects.all().last().max_loss:
            return Response(
                {
                    "error": "code",
                    "message": "You reached your 24h transaction limit"
                },
                status=400)

        response_body = dwolla_transaction(
            user=request.user,
            action=PaymentAction.WITHDRAW,
            **serializer.validated_data
        )
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
                status=400)

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
                    "message": "Payment method doesn't exist",
                    "payment_method": serializer.data["payment_method"]
                },
                status=400)
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
                },
                status=400)
        return Response(
            {
                "error": None,
                "message": "Successfully updated primary method",
                "payment_method": serializer.validated_data["payment_method"]
            }
        )


class GetFees(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses=FeeSerializer)
    def get(self, request, *args, **kwargs):
        fees = Fee.objects.all().last()
        serializer = FeeSerializer(fees)
        return Response(serializer.data)


class DwollaWebhook(views.APIView):
    def post(self, request, *args, **kwargs):
        dwolla_webhook_handler(request)
        # logging.getLogger().warning(f"{request.data = }")
        return Response()
