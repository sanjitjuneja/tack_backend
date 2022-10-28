import logging
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

import djstripe.models
import dwollav2
import plaid
import stripe
from django.core.exceptions import ObjectDoesNotExist

from core.choices import PaymentType, PaymentService, PaymentAction
from core.exceptions import InvalidActionError

from djstripe.models import Customer as dsCustomer
from djstripe.models import PaymentMethod as dsPaymentMethod
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample
from rest_framework import views, serializers
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
    calculate_transaction_loss, calculate_service_fee


logger = logging.getLogger("payments")


class AddBalanceStripe(views.APIView):
    """Endpoint for money refill from Stripe"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=AddBalanceStripeSerializer,
        responses=inline_serializer(
            name="add_balance_stripe_response",
            fields={
              "id": serializers.CharField(),
              "object": serializers.CharField(),
              "application": serializers.CharField(),
              "cancellation_reason": serializers.CharField(),
              "client_secret": serializers.CharField(),
              "created": serializers.IntegerField(),
              "customer": serializers.CharField(),
              "description": serializers.CharField(),
              "flow_directions": serializers.CharField(),
              "last_setup_error": serializers.CharField(),
              "latest_attempt": serializers.CharField(),
              "livemode": serializers.BooleanField(),
              "mandate": serializers.CharField(),
              "metadata": {},
              "next_action": serializers.CharField(),
              "on_behalf_of": serializers.CharField(),
              "payment_method": serializers.CharField(),
              "payment_method_options": {
                "card": {
                  "mandate_options": serializers.CharField(),
                  "network": serializers.CharField(),
                  "request_three_d_secure": serializers.CharField()
                }
              },
              "payment_method_types": [
                serializers.ChoiceField(choices=[("card", "Card")])
              ],
              "single_use_mandate": serializers.CharField(),
              "status": serializers.CharField(),
              "usage": serializers.CharField()
            }
        ),
        examples=[
            OpenApiExample(
                name="Stripe example",
                value={
                    "id": "seti_0LLoAbHRDqRuKWfqoTU94LQX",
                    "object": "setup_intent",
                    "application": None,
                    "cancellation_reason": None,
                    "client_secret": "seti_1LUoAbHUDqRuKWfqhTU99LQX_secret_MDEdKZgh36f6WeXXgroCfGSuwr2zICi",
                    "created": 1660035144,
                    "customer": None,
                    "description": None,
                    "flow_directions": None,
                    "last_setup_error": None,
                    "latest_attempt": None,
                    "livemode": False,
                    "mandate": None,
                    "metadata": {},
                    "next_action": None,
                    "on_behalf_of": None,
                    "payment_method": None,
                    "payment_method_options": {
                        "card": {
                          "mandate_options": None,
                          "network": None,
                          "request_three_d_secure": "automatic"
                        }
                    },
                    "payment_method_types": [
                        "card"
                    ],
                    "single_use_mandate": None,
                    "status": "requires_payment_method",
                    "usage": "off_session"
                }
            )
        ]
    )
    def post(self, request):
        serializer = AddBalanceStripeSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    "error": "Ox3",
                    "message": "Validation error. Some of the fields have invalid values",
                    "details": e.detail,
                },
                status=400)

        customer, created = dsCustomer.get_or_create(subscriber=request.user)

        # Calculate new amount because we charge fees
        amount_with_fees = calculate_amount_with_fees(
            amount=serializer.validated_data.get("amount"),
            service=PaymentService.STRIPE
        )

        sum24h = get_sum24h_transactions(user=request.user)
        current_transaction_loss = calculate_transaction_loss(
            amount=serializer.validated_data.get("amount"),
            service=PaymentService.STRIPE
        )

        logger.debug(f"{current_transaction_loss = }")
        total_loss = - (sum24h + current_transaction_loss)
        if total_loss >= Fee.objects.all().last().max_loss:
            return Response(
                {
                    "error": "Px1",
                    "message": "You reached your 24h transaction limit"
                },
                status=400)

        # TODO: try-except block
        payment_method = serializer.validated_data["payment_method"] or None
        logger.info(f"{payment_method = }")
        pi_request = {
            "customer": customer.id,
            "receipt_email": customer.email,
            "amount": amount_with_fees,
            "currency": serializer.validated_data["currency"]
        }
        if payment_method:
            pi_request["payment_method"] = payment_method
        logger.info(f"{pi_request = }")
        with transaction.atomic():
            pi = stripe.PaymentIntent.create(**pi_request)
            Transaction.objects.create(
                user=request.user,
                service_name=PaymentService.STRIPE if payment_method else PaymentService.DIGITAL_WALLET,
                action_type=PaymentAction.DEPOSIT,
                amount_requested=serializer.validated_data["amount"],
                amount_with_fees=amount_with_fees,
                fee_difference=current_transaction_loss,
                service_fee=calculate_service_fee(
                    amount=amount_with_fees,
                    service=PaymentService.STRIPE),
                transaction_id=pi["id"]
            )
            logger.info(f"{pi = }")
            logger.debug(f"{type(pi) = }")
            return Response(pi)


class AddBalanceDwolla(views.APIView):
    """Endpoint for money deposit from Dwolla"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=AddBalanceDwollaSerializer,
        responses=inline_serializer(
            name="add_balance_dwolla_response",
            fields={
              "id": serializers.CharField()
            }
        )
    )
    def post(self, request):
        serializer = AddBalanceDwollaSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    "error": "Ox3",
                    "message": "Validation error. Some of the fields have invalid values",
                    "details": e.detail,
                },
                status=400)
        amount = serializer.validated_data["amount"]
        payment_method = serializer.validated_data["payment_method"]

        sum24h = get_sum24h_transactions(user=request.user)
        current_transaction_loss = calculate_transaction_loss(
            amount=serializer.validated_data.get("amount"),
            service=PaymentService.STRIPE
        )
        logger.debug(f"{current_transaction_loss = }")
        total_loss = - (sum24h + current_transaction_loss)
        if total_loss >= Fee.objects.all().last().max_loss:
            return Response(
                {
                    "error": "Px1",
                    "message": "You reached your 24h transaction limit"
                },
                status=400)

        is_enough_funds = check_dwolla_balance(request.user, amount, payment_method)
        if not is_enough_funds:
            logger.info(f"NOT ENOUGH FUNDS from {request.user = }, {amount = }. {total_loss = }")
            return Response(
                {
                    "error": "Px2",
                    "message": "Insufficient funds"
                }, status=400)
        try:
            transaction_id = dwolla_transaction(
                user=request.user,
                action=PaymentAction.DEPOSIT,
                **serializer.validated_data
            )
            logger.info(f"AddBalanceDwolla {transaction_id = }")
        except InvalidActionError as e:
            logger.warning(f"InvalidActionError {e = }")
            return Response(
                {
                    "error": e.error,
                    "message": e.message,
                },
                status=e.status
            )
        except dwollav2.Error as e:
            logger.warning(f"dwollav2.Error {e = }")
            return Response(e.body)

        return Response(
            {
                "id": transaction_id
            },
            status=200
        )


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
        logger.debug(f"{ds_customer = }")
        pms = dsPaymentMethod.objects.filter(
            customer=ds_customer
        ).order_by(
            "-created"
        )
        logger.debug(f"{pms = }")
        serializer = StripePaymentMethodSerializer(pms, many=True)
        return Response(
            {
                "results": serializer.data
            }
        )


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
                    "error": "Ox1",
                    "message": "Can not find DB user"
                },
                status=400)

        try:
            pms = get_dwolla_payment_methods(ba.dwolla_user)
        except dwollav2.Error as e:
            return Response(e.body)

        data = update_dwolla_pms_with_primary(pms, request.user)
        serializer = DwollaPaymentMethodSerializer(data, many=True)
        return Response(
            {
                "results": serializer.data
            }
        )


class GetLinkToken(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses={
        200: inline_serializer(
            name="GetLinkToken",
            fields={
                "link_token": serializers.CharField()
            }
        )})
    def get(self, request):
        dwolla_id = get_dwolla_id(request.user)
        link_token = get_link_token(dwolla_id)
        return Response(
            {
                "link_token": link_token
            }
        )


class AddUserWithdrawMethod(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=AddWithdrawMethodSerializer, responses=DwollaPaymentMethodSerializer)
    def post(self, request, *args, **kwargs):
        serializer = AddWithdrawMethodSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            logger.error(f"INSIDE AddUserWithdrawMethod")
            logger.error(f"{e = }")
            return Response(
                {
                    "error": "Ox3",
                    "message": "Validation error. Some of the fields have invalid values",
                    "details": e.detail,
                },
                status=400)
        public_token = serializer.validated_data['public_token']
        logger.debug(f"{public_token = }")

        access_token = get_access_token(public_token)
        logger.debug(f"{access_token = }")
        save_dwolla_access_token(access_token, request.user)
        accounts = get_accounts_with_processor_tokens(access_token)
        logger.debug(f"{accounts = }")

        try:
            ba = BankAccount.objects.get(user=request.user)
        except BankAccount.DoesNotExist:
            # TODO: create dwolla account and return empty list
            return Response(
                {
                    "error": "Ox1",
                    "message": "Can not find DB user"
                },
                status=400)

        adding_first_bank = False if UserPaymentMethods.objects.filter(bank_account=ba).exists() else True

        try:
            attach_all_accounts_to_dwolla(request.user, accounts, access_token)
        except dwollav2.Error as e:
            logger.debug(f"dwollav2.Error")
            logger.error(f"{e = }")
            return Response(e.body, status=e.status)
        except plaid.ApiException as e:
            logger.debug(f"plaid.ApiException")
            logger.error(f"{e = }")
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
        logger.debug(f"{serializer.data = }")
        return Response(
            {
                "results": serializer.data
            }
        )


class DwollaMoneyWithdraw(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=DwollaMoneyWithdrawSerializer, responses=DwollaMoneyWithdrawSerializer)
    def post(self, request, *args, **kwargs):
        serializer = DwollaMoneyWithdrawSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    "error": "Ox3",
                    "message": "Validation error. Some of the fields have invalid values",
                    "details": e.detail,
                },
                status=400)
        if not request.user.allowed_to_withdraw:
            return Response(
                {
                    "error": "Px8",
                    "message": "You are not allowed to withdraw money"
                },
                status=400)
        try:
            ba = BankAccount.objects.get(user=request.user)
            if ba.usd_balance < serializer.validated_data["amount"]:
                return Response(
                    {
                        "error": "Px2",
                        "message": "Insufficient funds"
                    },
                    status=400)
        except BankAccount.DoesNotExist:
            pass

        sum24h = get_sum24h_transactions(user=request.user)
        current_transaction_loss = calculate_transaction_loss(
            amount=serializer.validated_data.get("amount"),
            service=PaymentService.DWOLLA
        )
        total_loss = - (sum24h + current_transaction_loss)
        if total_loss >= Fee.objects.all().last().max_loss:
            return Response(
                {
                    "error": "Px1",
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
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    "error": "Ox3",
                    "message": "Validation error. Some of the fields have invalid values",
                    "details": e.detail,
                },
                status=400)
        payment_method_id = serializer["pm_id"]
        ds_customer, created = djstripe.models.Customer.get_or_create(
            subscriber=request.user
        )
        try:
            pm = dsPaymentMethod.objects.get(id=payment_method_id, customer=ds_customer.id)
        except dsPaymentMethod.DoesNotExist:
            return Response(
                {
                    "error": "Px3",
                    "message": "Payment method not found"
                },
                status=400)

        return Response(StripePaymentMethodSerializer(pm))


class DetachPaymentMethod(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=DeletePaymentMethodSerializer, responses=DeletePaymentMethodSerializer)
    def post(self, request, *args, **kwargs):
        serializer = DeletePaymentMethodSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    "error": "Ox3",
                    "message": "Validation error. Some of the fields have invalid values",
                    "details": e.detail,
                },
                status=400)

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
                    "error": "Px4",
                    "message": "Payment method doesn't exist",
                    "payment_method": serializer.data["payment_method"]
                },
                status=400)
        return Response(
            {
                "error": None,
                "message": "Successfully detached",
                "payment_method": serializer.data["payment_method"]
            },
            status=200)


class SetPrimaryPaymentMethod(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=SetPrimaryPaymentMethodSerializer, responses=SetPrimaryPaymentMethodSerializer)
    def post(self, request, *args, **kwargs):
        serializer = SetPrimaryPaymentMethodSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    "error": "Ox3",
                    "message": "Validation error. Some of the fields have invalid values",
                    "details": e.detail,
                },
                status=400)
        try:
            set_primary_method(
                user=request.user,
                payment_type=serializer.validated_data["payment_type"],
                payment_method=serializer.validated_data["payment_method"]
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "Px4}",
                    "message": "Payment method does not exist",
                    "payment_method": serializer.validated_data["payment_method"]
                },
                status=400)
        return Response(
            {
                "error": None,
                "message": "Successfully updated primary method",
                "payment_method": serializer.validated_data["payment_method"]
            },
            status=200)


class GetFees(views.APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=None, responses=FeeSerializer)
    def get(self, request, *args, **kwargs):
        fees = Fee.objects.all().last()
        serializer = FeeSerializer(fees)
        return Response(serializer.data)


class DwollaWebhook(views.APIView):
    @extend_schema(request=inline_serializer(
        name="Dwolla_webhook",
        fields={
            "data": serializers.JSONField()
        }
    ), responses=None)
    def post(self, request, *args, **kwargs):
        dwolla_webhook_handler(request)
        # logging.getLogger().warning(f"{request.data = }")
        return Response()
