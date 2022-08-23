import logging
from decimal import Decimal, Context

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from djstripe.models import PaymentIntent
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

from core.choices import OfferType
from payment.plaid_service import plaid_client
from payment.dwolla_service import dwolla_client
from payment.models import BankAccount, UserPaymentMethods
from tack.models import Tack
from tackapp.settings import DWOLLA_MAIN_FUNDING_SOURCE
from user.models import User


@transaction.atomic
def send_payment_to_runner(tack: Tack):
    if tack.is_paid:
        return
    tack.runner.bankaccount.usd_balance += tack.price
    tack.is_paid = True
    tack.save()


def get_dwolla_payment_methods(dwolla_user_id):
    token = dwolla_client.Auth.client()
    response = token.get(f"customers/{dwolla_user_id}/funding-sources")
    return response.body


def get_link_token(dwolla_id_user):
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
                    [DepositoryAccountSubtype('checking'), DepositoryAccountSubtype('savings')]
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
    try:
        ba = BankAccount.objects.get(user=user)
    except ObjectDoesNotExist:
        return None
    return ba.dwolla_user


def get_access_token(public_token: str) -> str:
    exchange_request = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    exchange_response = plaid_client.item_public_token_exchange(exchange_request)
    access_token = exchange_response['access_token']
    return access_token


def get_bank_account_ids(access_token: str) -> list[dict]:
    request = AuthGetRequest(access_token=access_token)
    response = plaid_client.auth_get(request)
    supported_accounts = []
    for account in response.get('accounts'):
        if account.get('subtype') == "checking" and account.get('type') == "depository":
            supported_accounts.append(account)
    return supported_accounts


def get_accounts_with_processor_tokens(access_token: str) -> list[dict]:
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


def attach_all_accounts_to_dwolla(user: User, accounts: list) -> list[dict]:
    dwolla_id = get_dwolla_id(user)
    for account in accounts:
        payment_method_id = attach_account_to_dwolla(dwolla_id, account)

    account_names = [account["official_name"] for account in accounts]
    return account_names


def attach_account_to_dwolla(dwolla_id: str, account: dict) -> str:
    token = dwolla_client.Auth.client()
    response = token.post(f"customers/{dwolla_id}/funding-sources",
                          {"plaidToken": account.get("plaidToken"),
                           "name": account.get("name")})
    # TODO: error handling

    payment_method_id = response.headers["Location"].split("/")[-1]
    try:
        ba = BankAccount.objects.get(dwolla_user=dwolla_id)
        UserPaymentMethods.objects.create(bank_account=ba, dwolla_payment_method=payment_method_id)
    except BankAccount.DoesNotExist:
        logging.getLogger().warning(f"Bank Account of {dwolla_id} not found")
        # TODO: error handling

    return payment_method_id


@transaction.atomic
def add_money_to_bank_account(payment_intent: PaymentIntent):
    try:
        ba = BankAccount.objects.get(stripe_user=payment_intent.customer)
        ba.usd_balance += payment_intent.amount
        ba.save()
    except BankAccount.DoesNotExist:
        # TODO: Error handling/create BA
        logging.getLogger().warning(f"Bank account of {payment_intent.customer} is not found")


def save_dwolla_access_token(access_token: str, user: User):
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
):
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
        }
        # TODO: clearing + add to function argument
    }
    return transfer_request


def check_dwolla_balance(user: User, amount: int, payment_method: str = None):
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
    except ObjectDoesNotExist:
        pass
    return False


def convert_to_decimal(amount: int, currency: str = "USD") -> Decimal:
    currency_cents_dict = {
        "USD": 100,
        "EUR": 100
    }
    amount = Decimal(amount, Context(prec=2))
    return amount / currency_cents_dict[currency]


@transaction.atomic
def withdraw_dwolla_money(
        user: User,
        amount: int,
        payment_method: str,
        currency: str = "USD",
        *args,
        **kwargs):
    token = dwolla_client.Auth.client()
    transfer_request = get_transfer_request(
        source=DWOLLA_MAIN_FUNDING_SOURCE,
        destination=payment_method,
        currency=currency,
        amount=amount
    )
    response = token.post('transfers', transfer_request)
    logging.getLogger().warning(response.headers)
    logging.getLogger().warning(response.body)
    ba = BankAccount.objects.get(user=user)
    ba.usd_balance -= amount
    ba.save()
    return response.body


@transaction.atomic
def refill_dwolla_money(
        user: User,
        amount: int,
        payment_method: str,
        currency: str = "USD",
        *args,
        **kwargs):
    token = dwolla_client.Auth.client()
    transfer_request = get_transfer_request(
        source=payment_method,
        destination=DWOLLA_MAIN_FUNDING_SOURCE,
        currency=currency,
        amount=amount
    )
    response = token.post('transfers', transfer_request)
    logging.getLogger().warning(response.headers)
    logging.getLogger().warning(response.body)
    ba = BankAccount.objects.get(user=user)
    ba.usd_balance += amount
    ba.save()
    return response.body
