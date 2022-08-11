import djstripe.models
import stripe
from django.db.models.signals import post_save
from django.dispatch import receiver

from payment.models import BankAccount
from user.models import User


@receiver(signal=post_save, sender=User)
def create_stripe_account(instance: User, created: bool, *args, **kwargs):
    if created:
        # TODO: Create dwolla account + attach to BankAccount
        # API Stripe call to create a customer
        djstripe_customer, created = djstripe.models.Customer.get_or_create(
            subscriber=instance
        )
        # API Stripe call to set additional information about Customer
        stripe.Customer.modify(
            djstripe_customer.id,
            name=instance.get_full_name(),
            phone=instance.phone_number,
        )
        # Creating record in our system
        BankAccount.objects.create(
            user=instance,
            stripe_user=djstripe_customer.id
        )
