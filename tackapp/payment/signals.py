import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.choices import PaymentService

from djstripe import webhooks
from djstripe.models import PaymentIntent, PaymentMethod

from payment.models import StripePaymentMethodsHolder, Transaction, BankAccount
from payment.serializers import BankAccountSerializer
from payment.services import add_money_to_bank_account, calculate_service_fee
from tackapp.websocket_messages import WSSender

ws_sender = WSSender()
logger = logging.getLogger("payments")


@webhooks.handler("payment_intent.succeeded")
def add_balance_to_user(event, *args, **kwargs):

    logger.debug("payment.add_balance_to_user")
    pi = PaymentIntent.objects.get(id=event.data.get("object").get("id"))
    tr = Transaction.objects.get(transaction_id=pi.id)
    logger.debug(f"{pi =}")
    logger.debug(f"{tr =}")
    if tr.is_succeeded:  # already succeeded (probably duplicate)
        logger.info(f"Duplicate transaction {tr = }")
        return
    with transaction.atomic():
        if tr.is_succeeded:
            logger.debug(f"{tr} is already succeeded")
            return
        add_money_to_bank_account(payment_intent=pi, cur_transaction=tr)
        service_fee = calculate_service_fee(amount=pi.amount, service=PaymentService.STRIPE)
        logger.debug(f"{service_fee =}")
        tr.is_succeeded = True
        tr.save()
    logger.info(f"Added {tr.amount_requested} to {tr.user}")


@webhooks.handler("payment_method.attached")
def create_pm_holder(event, *args, **kwargs):
    instance = PaymentMethod.objects.get(id=event.data.get("object").get("id"))
    StripePaymentMethodsHolder.objects.create(stripe_pm=instance)


@receiver(signal=post_save, sender=BankAccount)
def ba_save(instance: BankAccount, *args, **kwargs):
    ws_sender.send_message(
        f"user_{instance.user.id}",
        'balance.update',
        BankAccountSerializer(instance).data)
