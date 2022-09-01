import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from djstripe import webhooks

from djstripe.models import PaymentIntent, PaymentMethod
from djstripe.signals import WEBHOOK_SIGNALS

from payment.models import StripePaymentMethodsHolder
from payment.services import add_money_to_bank_account


@receiver(signal=post_save, sender=PaymentIntent)
def add_balance_to_user(instance: PaymentIntent, created: bool, *args, **kwargs):
    if instance.status == "succeeded":
        add_money_to_bank_account(instance.amount)


@receiver(signal=WEBHOOK_SIGNALS.get("payment_method.attached"), sender=PaymentMethod)
def create_pm_holder(instance: PaymentMethod, created: bool, *args, **kwargs):
    logging.getLogger().warning(f"{kwargs = }")
    if created:
        spmh = StripePaymentMethodsHolder.objects.create(stripe_pm=instance)
        logging.getLogger().warning(f"{spmh = }")


@webhooks.handler("paymentmethod.attached")
def charge_dispute_created(event, **kwargs):
    logging.getLogger().warning(f"{kwargs = }")
    logging.getLogger().warning(f"{event = }")
    # spmh = StripePaymentMethodsHolder.objects.create(stripe_pm=instance)
    # logging.getLogger().warning(f"{spmh = }")
