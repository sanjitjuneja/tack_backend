from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from payment.models import BankAccount
from user.models import User
from user.services import create_api_accounts, deactivate_dwolla_customer, delete_stripe_customer


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


@receiver(signal=pre_delete, sender=User)
def delete_stripe_dwolla_account(instance: User, *args, **kwargs):
    deactivate_dwolla_customer(instance)
    delete_stripe_customer(instance)
