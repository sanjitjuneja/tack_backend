from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
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
from core.plaid_test import plaid_client
from payment.dwolla import dwolla_client
from payment.models import BankAccount
from tack.models import Tack
from user.models import User


@transaction.atomic
def send_payment_to_runner(tack: Tack):
    if tack.is_paid:
        return
    if tack.accepted_offer.offer_type == OfferType.OFFER:
        tack.runner.bankaccount.usd_balance += tack.price
        tack.is_paid = True
        tack.save()
    elif tack.accepted_offer.offer_type == OfferType.COUNTER_OFFER:
        tack.runner.bankaccount.usd_balance += tack.accepted_offer.price
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


def get_access_token(public_token):
    exchange_request = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    exchange_response = plaid_client.item_public_token_exchange(exchange_request)
    access_token = exchange_response['access_token']
    return access_token


def get_bank_account_ids(access_token):
    request = AuthGetRequest(access_token=access_token)
    response = plaid_client.auth_get(request)
    supported_accounts = []
    for account in response.get('accounts'):
        if account.get('subtype') == "checking" and account.get('type') == "depository":
            supported_accounts.append(account)
    return supported_accounts


def get_accounts_with_processor_tokens(access_token):
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


def attach_all_accounts_to_dwolla(user: User, accounts: list):
    dwolla_id = get_dwolla_id(user)
    for account in accounts:
        attach_account_to_dwolla(dwolla_id, account)


def attach_account_to_dwolla(dwolla_id, account):
    token = dwolla_client.Auth.client()
    response = token.post(f"customers/{dwolla_id}/funding-sources",
                          {"plaidToken": account.get("plaidToken"),
                           "name": account.get("name")})
    pm_id = response.headers["Location"].split("/")[-1]
    return pm_id
