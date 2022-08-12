import djstripe.models
import stripe
from django.db.models.signals import post_save
from django.dispatch import receiver

from payment.dwolla import dwolla_client
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
        token = dwolla_client.Auth.client()

        # TODO: Error handling
        response = token.post(
            "customers",
            {
                "firstName": instance.first_name,
                "lastName": instance.last_name,
                "email": instance.email,
                "correlationId": instance.id
            })
        dwolla_id = response.headers["Location"].split("/")[-1]

        # Creating record in our system
        BankAccount.objects.create(
            user=instance,
            stripe_user=djstripe_customer.id,
            dwolla_user=dwolla_id
        )
