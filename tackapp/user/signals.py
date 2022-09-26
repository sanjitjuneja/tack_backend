import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from payment.models import BankAccount
from tackapp.websocket_messages import WSSender
from user.models import User
from user.serializers import UserDetailSerializer
from user.services import create_api_accounts, deactivate_dwolla_customer, delete_stripe_customer


ws_sender = WSSender()
logger = logging.getLogger('django')


@receiver(signal=post_save, sender=User)
def create_stripe_dwolla_account(instance: User, created: bool, *args, **kwargs):
    if created and not instance.is_superuser:
        stripe_id, dwolla_id = create_api_accounts(instance)

        # Creating record in our system
        BankAccount.objects.create(
            user=instance,
            stripe_user=stripe_id,
            dwolla_user=dwolla_id
        )
    ws_sender.send_message(
        f"user_{instance.id}",
        'user.update',
        UserDetailSerializer(instance).data)


@receiver(signal=pre_delete, sender=User)
def delete_stripe_dwolla_account(instance: User, *args, **kwargs):
    deactivate_dwolla_customer(instance)
    delete_stripe_customer(instance)
