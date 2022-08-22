import asyncio

import djstripe.models
import stripe
from asgiref.sync import sync_to_async
from django.db.models.signals import post_save
from django.dispatch import receiver

from payment.dwolla_service import dwolla_client
from payment.models import BankAccount
from user.models import User
from user.services import create_api_accounts


@receiver(signal=post_save, sender=User)
def create_stripe_dwolla_account(instance: User, created: bool, *args, **kwargs):
    if created:
        stripe_id, dwolla_id = create_api_accounts(instance)
        # stripe_id, dwolla_id = await create_api_accounts(instance)
        print(f"{stripe_id = }, {dwolla_id = }")
        # Creating record in our system
        BankAccount.objects.create(
            user=instance,
            stripe_user=stripe_id,
            dwolla_user=dwolla_id
        )
    # TODO: if email/phone changes - update with services
