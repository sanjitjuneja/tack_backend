from djstripe.enums import PaymentIntentStatus

from djstripe import webhooks
from djstripe.models import PaymentIntent, PaymentMethod

from payment.models import StripePaymentMethodsHolder
from payment.services import add_money_to_bank_account


@webhooks.handler("payment_intent.succeeded")
def add_balance_to_user(event, *args, **kwargs):
    pi = PaymentIntent.objects.get(id=event.data.get("object").get("id"))
    if pi.status != PaymentIntentStatus.succeeded:
        add_money_to_bank_account(pi.amount)


@webhooks.handler("payment_method.attached")
def create_pm_holder(event, *args, **kwargs):
    instance = PaymentMethod.objects.get(id=event.data.get("object").get("id"))
    StripePaymentMethodsHolder.objects.create(stripe_pm=instance)
