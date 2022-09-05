from core.choices import PaymentService
from djstripe.enums import PaymentIntentStatus

from djstripe import webhooks
from djstripe.models import PaymentIntent, PaymentMethod

from payment.models import StripePaymentMethodsHolder, Transaction
from payment.services import add_money_to_bank_account, calculate_service_fee


@webhooks.handler("payment_intent.succeeded")
def add_balance_to_user(event, *args, **kwargs):
    pi = PaymentIntent.objects.get(id=event.data.get("object").get("id"))
    if pi.status != PaymentIntentStatus.succeeded:
        add_money_to_bank_account(pi.amount)
        service_fee = calculate_service_fee(amount=pi.amount, service=PaymentService.STRIPE)
        Transaction.objects.create(
            transaction_id=pi.id,
            is_stripe=True,
            amount_with_fees=pi.amount,
            service_fee=service_fee,
            is_succeeded=True
        )


@webhooks.handler("payment_method.attached")
def create_pm_holder(event, *args, **kwargs):
    instance = PaymentMethod.objects.get(id=event.data.get("object").get("id"))
    StripePaymentMethodsHolder.objects.create(stripe_pm=instance)
