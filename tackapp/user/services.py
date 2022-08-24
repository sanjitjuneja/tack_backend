from typing import OrderedDict
from uuid import uuid4
import aiohttp
import asyncio

import djstripe.models
import stripe
from django.db.models import Q

from payment.dwolla_service import dwolla_client
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

    response = token.post(
        "customers",
        {
            "firstName": user.first_name,
            "lastName": user.last_name,
            "email": user.email,
            "correlationId": user.id
        })
    dwolla_id = response.headers["Location"].split("/")[-1]
    return dwolla_id
