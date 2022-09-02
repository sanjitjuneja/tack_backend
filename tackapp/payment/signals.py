import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

import djstripe.models
from djstripe import webhooks

from djstripe.models import PaymentIntent, PaymentMethod
from djstripe.signals import WEBHOOK_SIGNALS

from payment.models import StripePaymentMethodsHolder
from payment.services import add_money_to_bank_account


@receiver(signal=post_save, sender=PaymentIntent)
def add_balance_to_user(instance: PaymentIntent, created: bool, *args, **kwargs):
    if instance.status == "succeeded":
        add_money_to_bank_account(instance.amount)


@receiver(signal=WEBHOOK_SIGNALS.get("payment_method.attached"))
def create_pm_holder(*args, **kwargs):
    evt = djstripe.models.Event.objects.get(id=kwargs.get("id"))
    logging.getLogger().warning(f"{evt = }")
    logging.getLogger().warning(f"{evt.data = }")
    instance = djstripe.models.PaymentMethod.objects.get(id=evt.data.get("object").get("id"))
    logging.getLogger().warning(f"{instance = }")
    spmh = StripePaymentMethodsHolder.objects.create(stripe_pm=instance)
    logging.getLogger().warning(f"{spmh = }")


# @receiver(signal=post_save, sender=PaymentMethod)
# def create_pm_holder(instance: PaymentMethod, created: bool, *args, **kwargs):
#     logging.getLogger().warning(f"{args = }")
#     logging.getLogger().warning(f"{kwargs = }")
#     logging.getLogger().warning(f"{instance = }")
#     if created:
#         spmh = StripePaymentMethodsHolder.objects.create(stripe_pm=instance)
#         logging.getLogger().warning(f"{spmh = }")
