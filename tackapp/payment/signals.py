import logging

from django.db import transaction

from core.choices import PaymentService
from djstripe.enums import PaymentIntentStatus

from djstripe import webhooks
from djstripe.models import PaymentIntent, PaymentMethod

from payment.models import StripePaymentMethodsHolder, Transaction
from payment.services import add_money_to_bank_account, calculate_service_fee


@webhooks.handler("payment_intent.succeeded")
def add_balance_to_user(event, *args, **kwargs):
    logger = logging.getLogger()
    logger.warning("add_balance_to_user")
    pi = PaymentIntent.objects.get(id=event.data.get("object").get("id"))
    logger.warning(f"{pi =}")
    add_money_to_bank_account(pi)
    service_fee = calculate_service_fee(amount=pi.amount, service=PaymentService.STRIPE)
    logger.warning(f"{service_fee =}")
    tr = Transaction.objects.get(transaction_id=pi.id)
    logger.warning(f"{tr =}")
    tr.is_succeeded = True
    tr.save()


@webhooks.handler("payment_method.attached")
def create_pm_holder(event, *args, **kwargs):
    instance = PaymentMethod.objects.get(id=event.data.get("object").get("id"))
    StripePaymentMethodsHolder.objects.create(stripe_pm=instance)
