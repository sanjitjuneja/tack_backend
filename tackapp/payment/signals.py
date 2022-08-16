from django.db.models.signals import post_save
from django.dispatch import receiver
from djstripe.models import PaymentIntent

from payment.services import add_money_to_bank_account


@receiver(signal=post_save, sender=PaymentIntent)
def add_balance_to_user(instance: PaymentIntent, created: bool, *args, **kwargs):
    if instance.status == "succeeded":
        add_money_to_bank_account(instance.amount)

