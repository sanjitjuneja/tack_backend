from django.db.models.signals import post_save
from django.dispatch import receiver
from djstripe.models import PaymentIntent, PaymentMethod

from payment.models import StripePaymentMethodsHolder
from payment.services import add_money_to_bank_account


@receiver(signal=post_save, sender=PaymentIntent)
def add_balance_to_user(instance: PaymentIntent, created: bool, *args, **kwargs):
    if instance.status == "succeeded":
        add_money_to_bank_account(instance.amount)


@receiver(signal=post_save, sender=PaymentMethod)
def create_pm_holder(instance: PaymentIntent, created: bool, *args, **kwargs):
    if created:
        StripePaymentMethodsHolder.objects.create(stripe_pm=instance)
