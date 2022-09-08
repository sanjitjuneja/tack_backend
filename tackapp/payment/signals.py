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


@webhooks.handler("payment_intent.succeeded")
def add_balance_to_user(event, *args, **kwargs):
    pi = PaymentIntent.objects.get(id=event.data.get("object").get("id"))
    if pi.status != PaymentIntentStatus.succeeded:
        ba = BankAccount.objects.get(stripe_user=pi.customer)
        add_money_to_bank_account(ba, pi)
        service_fee = calculate_service_fee(amount=pi.amount, service=PaymentService.STRIPE)
        try:
            Transaction.objects.get(
                transaction_id=pi.id,
                is_stripe=True,
                amount_with_fees=pi.amount,
                service_fee=service_fee,
                is_succeeded=True
            )
        except Transaction.DoesNotExist:
            # TODO: Something happened because Transaction should be created on AddBalanceStripe
            pass


@webhooks.handler("payment_method.attached")
def create_pm_holder(event, *args, **kwargs):
    instance = PaymentMethod.objects.get(id=event.data.get("object").get("id"))
    StripePaymentMethodsHolder.objects.create(stripe_pm=instance)


@receiver(signal=post_save, sender=BankAccount)
def ba_save(instance: BankAccount, *args, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{instance.user.id}",
        {
            'type': 'balance.update',
            'message': BankAccountSerializer(instance).data
        })
