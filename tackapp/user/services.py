import logging
from typing import OrderedDict
from uuid import uuid4
import aiohttp
import asyncio

import djstripe.models
import stripe
from djstripe.models import Customer as dsCustomer
from django.db.models import Q

from payment.dwolla_service import dwolla_client
from payment.models import DwollaRemovedAccount
from payment.services import get_dwolla_id, get_dwolla_payment_methods, deattach_dwolla_funding_sources, \
    _deactivate_dwolla_account, is_user_have_dwolla_pending_transfers
from review.models import Review
from user.models import User


def get_reviews_by_user(user):
    # Reviews where User.id is Tack.tacker or Tack.runner but not Review.user
    qs = Review.objects.filter(
        (Q(tack__tacker=user) | Q(tack__runner=user))
    ).exclude(
        user=user
    ).select_related(
        "tack"
    )
    return qs


def get_reviews_as_reviewer_by_user(user):
    qs = Review.objects.filter(user=user).select_related("tack")
    return qs


def user_change_bio(user: User, data: OrderedDict):
    for key, value in data.items():
        exec(f"user.{key} = value")
    user.save()
    dwolla_change_info(user)
    stripe_change_info(user)
    return user


def create_api_accounts(user: User):
    stripe_id = create_stripe_account(user)
    dwolla_id = create_dwolla_account(user)

    return stripe_id, dwolla_id


def create_stripe_account(user: User):
    # API Stripe call to create a customer
    djstripe_customer, created = djstripe.models.Customer.get_or_create(
        subscriber=user
    )
    # API Stripe call to set additional information about Customer
    stripe.Customer.modify(
        djstripe_customer.id,
        name=user.get_full_name(),
        phone=user.phone_number
    )
    return djstripe_customer.id


def create_dwolla_account(user: User):
    token = dwolla_client.Auth.client()
    logger = logging.getLogger()
    response = token.get(f"customers?email={user.email}")

    # if user already exists in Dwolla system we update information about him
    if response.body["total"] == 1:
        customer = response.body["_embedded"]["customers"][0]
        logger.warning("Found existing dwolla customer:", customer)

        request = {
            "firstName": user.first_name,
            "lastName": user.last_name,
        }
        if customer["status"] == "deactivated":
            request["status"] = "reactivated"
        # if suspended == bad
        token.post(f"customers/{customer['id']}", request)
        dwolla_id = customer["id"]
    else:
        response = token.post(
            "customers",
            {
                "firstName": user.first_name,
                "lastName": user.last_name,
                "email": user.email,
            })
        dwolla_id = response.headers["Location"].split("/")[-1]
    return dwolla_id


def dwolla_change_info(user: User):
    token = dwolla_client.Auth.client()

    dwolla_id = get_dwolla_id(user)
    request = {
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email
    }
    token.post(f"customers/{dwolla_id}", request)


def stripe_change_info(user: User):
    customer, created = dsCustomer.get_or_create(subscriber=user)
    stripe.Customer.modify(
        customer.id,
        name=user.get_full_name(),
        phone=user.phone_number,
        email=user.email
    )


def deactivate_dwolla_customer(user: User):
    dwolla_user_id = get_dwolla_id(user)

    # Remove all Dwolla funding sources and
    # Deactivate account if User have no pending transfers
    if not is_user_have_dwolla_pending_transfers(dwolla_user_id):
        deattach_dwolla_funding_sources(dwolla_user_id)
        _deactivate_dwolla_account(dwolla_user_id)

    # If Dwolla user have pending transfers - create row with his account
    DwollaRemovedAccount.objects.create(dwolla_id=dwolla_user_id)


def delete_stripe_customer(user: User):
    customer, created = dsCustomer.get_or_create(subscriber=user)
    stripe.Customer.delete(customer.id)
