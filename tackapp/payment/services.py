import logging
from decimal import Decimal, Context

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
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

from core.choices import OfferType, PaymentType
from dwolla_service.models import DwollaEvent
from payment.plaid_service import plaid_client
from payment.dwolla_service import dwolla_client
from payment.models import BankAccount, UserPaymentMethods, Fee, StripePaymentMethodsHolder
from tack.models import Tack
from tackapp.settings import DWOLLA_MAIN_FUNDING_SOURCE
from user.models import User


@transaction.atomic
def send_payment_to_runner(tack: Tack):
    """Transact money from one BankAccount to another"""

    if tack.is_paid:
        return
    tack.runner.bankaccount.usd_balance += tack.price
    tack.is_paid = True
    tack.save()


def get_dwolla_payment_methods(dwolla_user_id):
    """Get all funding-sources by Dwolla customer id"""

    # payment_methods = UserPaymentMethods.objects.filter(bank_account__dwolla_user=dwolla_user_id)

    token = dwolla_client.Auth.client()
    response = token.get(f"customers/{dwolla_user_id}/funding-sources")
    logging.getLogger().warning(f"{response = }")
    return response.body


def get_link_token(dwolla_id_user):
    """Get link token for FE to initiate plaid authentication"""

    request = LinkTokenCreateRequest(
        products=[Products('transactions')],  # , Products("identity_verification")],
        client_name="Plaid Test App",
        country_codes=[CountryCode('US')],
        language='en',
        # webhook='https://sample-webhook-uri.com',
        # link_customization_name='default',
        account_filters=LinkTokenAccountFilters(
            depository=DepositoryFilter(
                account_subtypes=DepositoryAccountSubtypes(
                    [
                        DepositoryAccountSubtype('checking'),
                        # DepositoryAccountSubtype('savings')
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
    logger = logging.getLogger()
    supported_accounts = []
    for account in response.get('accounts'):
        if account.subtype == AccountSubtype("checking") and account.type == AccountType("depository"):
            logger.warning(f"supported {account = }")
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


def attach_all_accounts_to_dwolla(user: User, accounts: list) -> list:
    """Attach and return all Dwolla payment methods to our BankAccount"""

    payment_methods = []
    dwolla_id = get_dwolla_id(user)
    for account in accounts:
        payment_method_id = attach_account_to_dwolla(dwolla_id, account)
        payment_methods.append(payment_method_id)

    return payment_methods


def attach_account_to_dwolla(dwolla_id: str, account: dict) -> str:
    """Attach one Dwolla payment method to our Tack BankAccount"""

    payment_method_id = get_dwolla_pm_by_plaid_token(dwolla_id, account)
    add_dwolla_payment_method(dwolla_id, payment_method_id)
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


def add_dwolla_payment_method(dwolla_id, dwolla_pm_id):
    """Make record in DB about Dwolla payment method"""

    try:
        ba = BankAccount.objects.get(dwolla_user=dwolla_id)
        UserPaymentMethods.objects.create(bank_account=ba, dwolla_payment_method=dwolla_pm_id)
    except BankAccount.DoesNotExist:
        logging.getLogger().warning(f"Bank Account of {dwolla_id} is not found")
        # TODO: error handling


@transaction.atomic
def add_money_to_bank_account(payment_intent: PaymentIntent):
    """Add balance to User BankAccount based on Stripe PaymentIntent when succeeded"""

    try:
        ba = BankAccount.objects.get(stripe_user=payment_intent.customer)
        ba.usd_balance += payment_intent.amount
        ba.save()
    except BankAccount.DoesNotExist:
        # TODO: Error handling/create BA
        logging.getLogger().warning(f"Bank account of {payment_intent.customer} is not found")


def save_dwolla_access_token(access_token: str, user: User):
    """Save Dwolla access token to DB. It will needed for bank balance check"""

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
    """Check """

    ba = BankAccount.objects.get(user=user)
    amount = convert_to_decimal(amount)
    request = AccountsBalanceGetRequest(
        access_token=ba.dwolla_access_token
    )
    response = plaid_client.accounts_balance_get(request)
    try:
        payment_method_qs = UserPaymentMethods.objects.get(
            bank_account__user=user,
            dwolla_payment_method=payment_method
        )
        dwolla_payment_id = payment_method_qs.dwolla_payment_method
        for account in response['accounts']:
            if account["account_id"] == dwolla_payment_id:
                logging.getLogger().warning(Decimal(account["balances"]["available"]))

                if Decimal(account["balances"]["available"], Context(prec=2)) >= amount:
                    return True
    except UserPaymentMethods.DoesNotExist:
        pass
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
        channel: str,
        action: str,
        currency: str = "USD",
        *args,
        **kwargs
):
    if action == "withdraw":
        source = DWOLLA_MAIN_FUNDING_SOURCE
        destination = payment_method
        amount_with_fees = amount
        if channel == "next-available":
            amount_with_fees = calculate_amount_with_fees(amount)
    elif action == "refill":
        source = payment_method
        destination = DWOLLA_MAIN_FUNDING_SOURCE
        amount_with_fees = amount
    else:
        return {"error": "code", "message": f"Invalid action: {action}"}

    transfer_request = get_transfer_request(
        source=source,
        destination=destination,
        currency=currency,
        amount=amount_with_fees,
        channel=channel
    )

    token = dwolla_client.Auth.client()
    response = token.post('transfers', transfer_request)
    logging.getLogger().warning(response.body)
    ba = BankAccount.objects.get(user=user)

    if action == "withdraw":
        ba.usd_balance -= amount
        ba.save()
    elif action == "refill":
        ba.usd_balance += amount
        ba.save()
    return response.body


def calculate_amount_with_fees(amount: int) -> int:
    fees = Fee.objects.all().last()
    abs_fee = amount * fees.fee_percent / 100
    if abs_fee < fees.fee_min:
        abs_fee = fees.fee_min
    elif abs_fee > fees.fee_max:
        abs_fee = fees.fee_max

    amount = int(amount + abs_fee)
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

    DwollaEvent.objects.create(
        event_id=request.data.get("id"),
        topic=request.data.get("topic"),
        timestamp=request.data.get("timestamp"),
        self_res=request.data.get("_links").get("self"),
        account=request.data.get("_links").get("account"),
        resource=request.data.get("_links").get("resource"),
        customer=request.data.get("_links").get("customer"),
        created=request.data.get("created"),
    )


def detach_dwolla_funding_sources(dwolla_id):
    funding_sources = get_dwolla_payment_methods(dwolla_id)

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
    if response.body["total"] == 0:
        return False
    return True


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
        stripe_pm = stripe_pms.get(stripe_pm=payment_method)
        stripe_pm.is_primary = True
        stripe_pm.save()


def detach_payment_method(user: User, payment_type: str, payment_method: str):
    if payment_type == PaymentType.BANK:
        UserPaymentMethods.objects.get(bank_account__user=user, dwolla_payment_method=payment_method)
        detach_dwolla_funding_source(payment_method)
    elif payment_type == PaymentType.CARD:
        dsPaymentMethod.objects.get(customer__subscriber=user, id=payment_method)
        detach_stripe_payment_method(payment_method)
