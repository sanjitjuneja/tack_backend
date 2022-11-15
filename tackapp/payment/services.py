import logging
from datetime import timedelta
from decimal import Decimal, Context
from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, F, Sum
from django.utils import timezone

from core.exceptions import InvalidActionError
from djstripe.models import PaymentIntent
from djstripe.models import PaymentMethod as dsPaymentMethod
from plaid.model.account_base import AccountBase
from plaid.model.account_subtype import AccountSubtype
from plaid.model.account_type import AccountType
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.depository_account_subtype import DepositoryAccountSubtype
from plaid.model.depository_account_subtypes import DepositoryAccountSubtypes
from plaid.model.depository_filter import DepositoryFilter
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_account_filters import LinkTokenAccountFilters
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.processor_token_create_request import ProcessorTokenCreateRequest
from plaid.model.products import Products

from core.choices import PaymentType, PaymentService, PaymentAction
from dwolla_service.models import DwollaEvent
from payment.plaid_service import plaid_client
from payment.dwolla_service import dwolla_client
from payment.models import BankAccount, UserPaymentMethods, Fee, StripePaymentMethodsHolder, Transaction, ServiceFee
from tack.models import Tack
from tackapp.settings import DWOLLA_MAIN_FUNDING_SOURCE
from user.models import User


logger = logging.getLogger("payments")


@transaction.atomic
def send_payment_to_runner(tack: Tack):
    """Transact money from one BankAccount to another"""

    logger.debug("INSIDE send_payment_to_runner")
    if tack.is_paid:
        logger.debug("if tack.is_paid:")
        return True
    tack.runner.bankaccount.deposit(amount=tack.price)
    return True


def get_dwolla_payment_methods(dwolla_user_id):
    """Get all funding-sources by Dwolla customer id"""

    # payment_methods = UserPaymentMethods.objects.filter(bank_account__dwolla_user=dwolla_user_id)

    token = dwolla_client.Auth.client()
    response = token.get(f"customers/{dwolla_user_id}/funding-sources?removed=false")
    logger.debug(f"{response.body = }")
    return response.body


def get_link_token(dwolla_id_user):
    """Get link token for FE to initiate plaid authentication"""

    request = LinkTokenCreateRequest(
        products=[Products('auth')],
        client_name="TEST TACKAPP",
        country_codes=[CountryCode('US')],
        language='en',
        # webhook='https://sample-webhook-uri.com',
        # link_customization_name='default',
        account_filters=LinkTokenAccountFilters(
            depository=DepositoryFilter(
                account_subtypes=DepositoryAccountSubtypes(
                    [
                        DepositoryAccountSubtype('checking'),
                    ]
                )
            )
        ),
        user=LinkTokenCreateRequestUser(
            client_user_id=dwolla_id_user
        )
    )

    link_token = plaid_client.link_token_create(request)
    return link_token['link_token']


def get_dwolla_id(user: User):
    """Get Dwolla customer id by User record in our system"""

    try:
        ba = BankAccount.objects.get(user=user)
    except ObjectDoesNotExist:
        return None
    return ba.dwolla_user


def get_access_token(public_token: str) -> str:
    """Get access token from Plaid for further interaction with it to retrieve processor-token"""

    exchange_request = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    exchange_response = plaid_client.item_public_token_exchange(exchange_request)
    access_token = exchange_response['access_token']
    return access_token


def get_bank_account_ids(access_token: str) -> list[AccountBase]:
    """Get all supported bank accounts(checking+depository) to manage from Plaid"""

    request = AuthGetRequest(access_token=access_token)
    response = plaid_client.auth_get(request)
    supported_accounts = []
    for account in response.get('accounts'):
        if account.subtype == AccountSubtype("checking") and account.type == AccountType("depository"):
            logger.debug(f"supported {account = }")
            supported_accounts.append(account)
    return supported_accounts


def get_accounts_with_processor_tokens(access_token: str) -> list[AccountBase]:
    """Get all accounts with Plaid processor-token"""

    accounts = get_bank_account_ids(access_token)

    for account in accounts:
        request = ProcessorTokenCreateRequest(
            access_token=access_token,
            account_id=account.get("account_id"),
            processor="dwolla"
        )
        response = plaid_client.processor_token_create(request)
        processor_token = response.get("processor_token")
        account["plaidToken"] = processor_token

    return accounts


def attach_all_accounts_to_dwolla(user: User, accounts: list, access_token: str) -> list:
    """Attach and return all Dwolla payment methods to our BankAccount"""

    payment_methods = []
    dwolla_id = get_dwolla_id(user)
    for account in accounts:
        payment_method_id = attach_account_to_dwolla(dwolla_id, account, access_token)
        payment_methods.append(payment_method_id)

    return payment_methods


def attach_account_to_dwolla(dwolla_id: str, account: dict, access_token: str) -> str:
    """Attach one Dwolla payment method to our Tack BankAccount"""

    payment_method_id = get_dwolla_pm_by_plaid_token(dwolla_id, account)
    add_dwolla_payment_method(dwolla_id, payment_method_id, account["account_id"], access_token)
    return payment_method_id


def get_dwolla_pm_by_plaid_token(dwolla_customer_id, pm_account):
    """Exchange plaidToken for Dwolla payment method"""

    token = dwolla_client.Auth.client()
    response = token.post(
        f"customers/{dwolla_customer_id}/funding-sources",
        {
            "plaidToken": pm_account.get("plaidToken"),
            "name": pm_account.get("name")
        }
    )
    return response.headers["Location"].split("/")[-1]


def add_dwolla_payment_method(dwolla_id, dwolla_pm_id, account_id=None, access_token=None):
    """
    Make record in DB about Dwolla payment method and related Plaid information
    :param dwolla_id: User id in Dwolla API
    :param dwolla_pm_id: Payment method id in Dwolla API
    :param account_id: Bank id in Plaid API
    :param access_token: access token for this Bank in Plaid API
    :return: None
    """

    try:
        ba = BankAccount.objects.get(dwolla_user=dwolla_id)
        UserPaymentMethods.objects.create(
            bank_account=ba,
            dwolla_payment_method=dwolla_pm_id,
            plaid_account_id=account_id,
            dwolla_access_token=access_token
        )
    except BankAccount.DoesNotExist:
        logger.error(f"Bank Account of {dwolla_id} is not found")
        # TODO: error handling


@transaction.atomic
def add_money_to_bank_account(payment_intent: PaymentIntent, cur_transaction: Transaction):
    """Add balance to User BankAccount based on Stripe PaymentIntent when succeeded"""
    try:
        logger.debug(f"add_money_to_bank_account {payment_intent.customer.id = }")
        ba = BankAccount.objects.get(
            stripe_user=payment_intent.customer.id
        )
        logger.debug(f"{ba = }")
        ba.deposit(
            amount=cur_transaction.amount_requested
        )
        logger.debug(f"{ba = }")
    except BankAccount.DoesNotExist:
        # TODO: Error handling/create BA
        logger.error(f"Bank account of {payment_intent.customer} is not found")


def save_dwolla_access_token(access_token: str, user: User):
    """Save Dwolla access token to DB. It will be needed for bank balance check"""

    try:
        ba = BankAccount.objects.get(user=user)
        ba.dwolla_access_token = access_token
        ba.save()
    except BankAccount.DoesNotExist:
        # TODO: error handling/creating new BA
        pass


def get_transfer_request(
        source: str,
        destination: str,
        currency: str,
        amount: int | Decimal,
        channel: str
):
    """Form Dwolla transaction request"""

    if type(amount) is int:
        amount = convert_to_decimal(amount, currency)
    transfer_request = {
        '_links': {
            'source': {
                'href': f'https://api-sandbox.dwolla.com/funding-sources/{source}'
            },
            'destination': {
                'href': f'https://api-sandbox.dwolla.com/funding-sources/{destination}'
            }
        },
        'amount': {
            'currency': currency,
            'value': str(amount)
        },
    }

    if channel == "real-time-payments":
        transfer_request["processingChannel"] = {
            "destination": "real-time-payments",
        }
    elif channel == "next-available":
        transfer_request["clearing"] = {
            'source': 'next-available',
            'destination': 'next-available'
        }

    return transfer_request


def check_dwolla_balance(user: User, amount: int, payment_method: str = None):
    """Check Active Bank balance"""

    pm = UserPaymentMethods.objects.get(dwolla_payment_method=payment_method)
    amount = convert_to_decimal(amount)
    request = AccountsBalanceGetRequest(
        access_token=pm.dwolla_access_token
    )
    response = plaid_client.accounts_balance_get(request)
    logger.debug(f"plaid {response = }")
    try:
        payment_method_qs = UserPaymentMethods.objects.get(
            bank_account__user=user,
            dwolla_payment_method=payment_method
        )
        dwolla_payment_id = payment_method_qs.dwolla_payment_method
        for account in response['accounts']:
            if account["account_id"] == pm.plaid_account_id:
                logger.debug(f"{Decimal(account['balances']['available']) = }")

                if Decimal(account["balances"]["available"], Context(prec=2)) >= amount:
                    return True
    except UserPaymentMethods.DoesNotExist:
        logger.error("payment.services.check_dwolla_balance: UserPaymentMethods.DoesNotExist")
    return False


def convert_to_decimal(amount: int, currency: str = "USD") -> Decimal:
    """Convert int value to Decimal based on currency"""

    currency_cents_dict = {
        "USD": 100,
        "EUR": 100
    }
    amount = Decimal(amount, Context(prec=2))
    return amount / currency_cents_dict[currency]


@transaction.atomic
def dwolla_transaction(
        user: User,
        amount: int,
        payment_method: str,
        action: str,
        channel: str = "ach",
        currency: str = "USD",
        *args,
        **kwargs
):
    if action == PaymentAction.WITHDRAW:
        source = DWOLLA_MAIN_FUNDING_SOURCE
        destination = payment_method
        amount_with_fees = amount
        if channel == "next-available":
            amount_with_fees = calculate_amount_with_fees(amount, service=PaymentService.DWOLLA)
    elif action == PaymentAction.DEPOSIT:
        source = payment_method
        destination = DWOLLA_MAIN_FUNDING_SOURCE
        amount_with_fees = amount
    else:
        logger.error("payment.services.dwolla_transaction: InvalidActionError")
        raise InvalidActionError(
            error="Px7",
            message=f"Invalied action: {action}",
            status=400
        )

    transfer_request = get_transfer_request(
        source=source,
        destination=destination,
        currency=currency,
        amount=amount_with_fees,
        channel=channel
    )
    logger.debug(f"payment.services.dwolla_transaction: {transfer_request = }")
    token = dwolla_client.Auth.client()
    response = token.post('transfers', transfer_request)
    transaction_id = response.headers["Location"].split("/")[-1]
    service_fee = calculate_service_fee(amount=amount, service=PaymentService.DWOLLA)
    logger.debug(response.body)
    ba = BankAccount.objects.get(user=user)
    current_transaction_loss = calculate_transaction_loss(
        amount=amount,
        service=PaymentService.DWOLLA
    )
    Transaction.objects.create(
        user=user,
        transaction_id=transaction_id,
        service_name=PaymentService.DWOLLA,
        amount_requested=amount,
        amount_with_fees=amount_with_fees,
        fee_difference=current_transaction_loss,
        service_fee=service_fee,
        action_type=action
    )
    match action:
        case PaymentAction.DEPOSIT:
            ba.deposit(amount=amount)
        case PaymentAction.WITHDRAW:
            ba.withdraw(amount=amount)

    return transaction_id


def calculate_amount_with_fees(amount: int, service: PaymentService) -> int:
    """
    Function that calculates new amount based on Fee that we charge users
    :param amount: amount in absolute minimal values e.g. cents
    :param service: service name e.g. "stripe", "dwolla"
    :return: new calculated amount
    """
    fees = Fee.objects.all().last()
    abs_fee = 0
    match service:
        case PaymentService.STRIPE:
            abs_fee = amount * fees.fee_percent_stripe / 100
            if abs_fee < fees.fee_min_stripe:
                abs_fee = fees.fee_min_stripe
            elif abs_fee > fees.fee_max_stripe and fees.fee_max_stripe:
                abs_fee = fees.fee_max_stripe
        case PaymentService.DWOLLA:
            abs_fee = amount * fees.fee_percent_dwolla / 100
            if abs_fee < fees.fee_min_dwolla:
                abs_fee = fees.fee_min_dwolla
            elif abs_fee > fees.fee_max_dwolla and fees.fee_max_dwolla:
                abs_fee = fees.fee_max_dwolla

    amount = int(amount + abs_fee)
    logger.debug(f"{amount = }")
    return amount


def get_dwolla_pms_by_id(pms_id: list):
    token = dwolla_client.Auth.client()
    responses = []
    for pm in pms_id:
        response = token.get(f"funding-sources/{pm}")
        responses.append(response.body)
    return responses


def dwolla_webhook_handler(request):
    # TODO: check hash

    try:
        DwollaEvent.objects.get(event_id=request.data.get("id"))
        return
    except DwollaEvent.DoesNotExist:
        pass

    topic = request.data.get("topic")
    DwollaEvent.objects.create(
        event_id=request.data.get("id"),
        topic=topic,
        timestamp=request.data.get("timestamp"),
        self_res=request.data.get("_links").get("self"),
        account=request.data.get("_links").get("account"),
        resource=request.data.get("_links").get("resource"),
        customer=request.data.get("_links").get("customer"),
        created=request.data.get("created"),
    )
    match topic:
        case "transfer_completed" | "customer_transfer_completed" | "bank_transfer_completed":
            transfer_id = request.data.get("_links").get("resource").get("href").split("/")[-1]
            try:
                trnsctn = Transaction.objects.get(transaction_id=transfer_id)
                trnsctn.is_succeeded = True
                trnsctn.save()
            except Transaction.DoesNotExist:
                pass
            except Transaction.MultipleObjectsReturned:
                pass


def detach_dwolla_funding_sources(dwolla_id):
    funding_sources = get_dwolla_payment_methods(dwolla_id)['_embedded']['funding-sources']

    logger.debug(f"in detach_dwolla_funding_sources: {funding_sources = }")
    for funding_source in funding_sources:
        detach_dwolla_funding_source(funding_source['id'])


def detach_dwolla_funding_source(funding_source_id):
    token = dwolla_client.Auth.client()
    token.post(
        f"funding-sources/{funding_source_id}",
        {"removed": True}
    )


def detach_stripe_payment_method(payment_method: str):
    payment_method = dsPaymentMethod.objects.get(
        id=payment_method
    )
    dsPaymentMethod.detach(payment_method)


def _deactivate_dwolla_account(dwolla_id):
    token = dwolla_client.Auth.client()
    token.post(
        f"customers/{dwolla_id}",
        {"status": "deactivated"}
    )


def is_user_have_dwolla_pending_transfers(dwolla_id):
    token = dwolla_client.Auth.client()
    response = token.get(f"customers/{dwolla_id}/transfers?status=pending")
    return bool(response.body["total"])


def set_primary_method(user: User, payment_type: str, payment_method: str):
    dwolla_pms = UserPaymentMethods.objects.filter(bank_account__user=user)
    dwolla_pms.update(is_primary=False)
    stripe_pms = StripePaymentMethodsHolder.objects.filter(stripe_pm__customer__subscriber=user)
    stripe_pms.update(is_primary=False)

    if payment_type == PaymentType.BANK:
        dwolla_pm = dwolla_pms.get(dwolla_payment_method=payment_method)
        dwolla_pm.is_primary = True
        dwolla_pm.save()
    elif payment_type == PaymentType.CARD:
        stripe_pm = stripe_pms.get(stripe_pm__id=payment_method)
        stripe_pm.is_primary = True
        stripe_pm.save()


def detach_payment_method(user: User, payment_type: str, payment_method: str):
    if payment_type == PaymentType.BANK:
        upm = UserPaymentMethods.objects.get(bank_account__user=user, dwolla_payment_method=payment_method)
        detach_dwolla_funding_source(payment_method)
        upm.delete()
    elif payment_type == PaymentType.CARD:
        dsPaymentMethod.objects.get(customer__subscriber=user, id=payment_method)
        detach_stripe_payment_method(payment_method)


def update_dwolla_pms_with_primary(pms: dict, user: User):
    """Enrich (data: list) of (funding_source's: dict) (is_primary: bool) values"""

    data = pms["_embedded"]["funding-sources"]
    dwolla_pm_ids = [funding_source["id"] for funding_source in data]

    # [{"dwolla_payment_method": "id-1", "is_primary": bool}, ...]
    upms_values = UserPaymentMethods.objects.filter(
        dwolla_payment_method__in=dwolla_pm_ids
    ).values(
        "dwolla_payment_method",
        "is_primary"
    )

    # Additional check if retrieved funding-sources from Dwolla API matched our UserPaymentMethods model
    if len(data) != len(upms_values):
        # TODO: add UserPaymentMethods
        for dwolla_pm_id in dwolla_pm_ids:
            if dwolla_pm_id not in upms_values.values_list("dwolla_payment_method", flat=True):
                dwolla_id = BankAccount.objects.get(user=user).dwolla_user
                add_dwolla_payment_method(dwolla_id, dwolla_pm_id)

        upms_values = UserPaymentMethods.objects.filter(
            dwolla_payment_method__in=dwolla_pm_ids
        ).values(
            "dwolla_payment_method",
            "is_primary"
        )

    # [{"id-1": bool}, ...]
    upms_dict = {
        upm['dwolla_payment_method']: upm['is_primary']
        for upm in upms_values
    }
    data = [
        funding_source | {'is_primary': upms_dict.get(funding_source['id']) or False}
        for funding_source in data
    ]
    return data


def calculate_service_fee(amount: int, service: PaymentService):
    service_fee = ServiceFee.objects.last()
    match service:
        case PaymentService.DWOLLA:
            logger.debug("calculate_service_fee, DWOLLA")
            logger.debug(int(amount * service_fee.dwolla_percent / 100 + service_fee.dwolla_const_sum))
            return int(amount * service_fee.dwolla_percent / 100 + service_fee.dwolla_const_sum)
        case PaymentService.STRIPE:
            logger.debug("calculate_service_fee, STRIPE")
            logger.debug(int(amount * service_fee.stripe_percent / 100 + service_fee.stripe_const_sum))
            return int(amount * service_fee.stripe_percent / 100 + service_fee.stripe_const_sum)


def get_sum24h_transactions(user: User) -> int:
    sum24h = Transaction.objects.filter(
                Q(service_name=PaymentService.STRIPE, is_succeeded=True) | Q(service_name=PaymentService.DWOLLA),
                user=user,
                creation_time__gt=timezone.now() - timedelta(hours=24)
            ).aggregate(
                sum24h=Sum(
                    F('amount_with_fees') - F('amount_requested') - F('service_fee')
                )
            )['sum24h']
    return sum24h if sum24h else 0


def calculate_transaction_loss(amount: int, service: PaymentService):
    logger.debug("INSIDE calculate_transaction_loss")
    amount_with_fees = calculate_amount_with_fees(amount=amount, service=service)
    service_fee = calculate_service_fee(amount=amount_with_fees, service=service)
    logger.debug(f"{service_fee = }")
    logger.debug(f"{amount_with_fees = }")
    return amount_with_fees - amount - service_fee


@transaction.atomic
def add_money_to_bank_account_custom(cur_transaction: Transaction):
    """Add balance to User BankAccount based on Stripe PaymentIntent when succeeded"""

    try:
        ba = BankAccount.objects.get(user=cur_transaction.user)
        ba.deposit(amount=cur_transaction.amount_requested)
    except BankAccount.DoesNotExist:
        # TODO: Error handling/create BA
        pass
        # logger.error(f"Bank account of {payment_intent.customer} is not found")
