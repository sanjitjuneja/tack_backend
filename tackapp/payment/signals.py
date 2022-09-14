import logging

from django.db import transaction

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.choices import PaymentService
from djstripe.enums import PaymentIntentStatus

from djstripe import webhooks
from djstripe.models import PaymentIntent, PaymentMethod

from payment.models import StripePaymentMethodsHolder, Transaction, BankAccount
from payment.serializers import BankAccountSerializer
from payment.services import add_money_to_bank_account, calculate_service_fee
from tackapp.websocket_messages import WSSender

ws_sender = WSSender()


@webhooks.handler("payment_intent.succeeded")
def add_balance_to_user(event, *args, **kwargs):
    logger = logging.getLogger()
    logger.warning("add_balance_to_user")
    pi = PaymentIntent.objects.get(id=event.data.get("object").get("id"))
    tr = Transaction.objects.get(transaction_id=pi.id)
    logger.warning(f"{pi =}")
    add_money_to_bank_account(payment_intent=pi, cur_transaction=tr)
    service_fee = calculate_service_fee(amount=pi.amount, service=PaymentService.STRIPE)
    logger.warning(f"{service_fee =}")

    logger.warning(f"{tr =}")
    tr.is_succeeded = True
    tr.save()


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
