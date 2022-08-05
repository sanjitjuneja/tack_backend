import stripe
from django.db.models.signals import post_save
from django.dispatch import receiver

from payment.models import BankAccount
from user.models import User


@receiver(signal=post_save, sender=User)
def assign_tack_with_group(instance: User, created: bool, *args, **kwargs):
    if created:
        customer = stripe.Customer.create(
            email=instance.email,
            name=instance.get_full_name(),
            phone=instance.phone_number
        )
        # BankAccount.objects.create(user=instance, stripe_user=customer.id)
