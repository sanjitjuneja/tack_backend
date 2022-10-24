import logging

import stripe
from django.db import transaction

from payment.models import Transaction
from djstripe.models import PaymentIntent as dsPaymentIntent
from payment.services import add_money_to_bank_account
from tack.models import Tack

logger = logging.getLogger('django')


def stripe_desync_check(request, transaction_id):
    """
    Fix for desync between FrontEnd and BackEnd
    This needs because FE gets response from Stripe immediately
    and thinks that our user have enough money to accept offer
    BE gets response on webhook after some amount of time
    This function only fixes our Transaction model but not djstripe models.
    Djstripe models should be updated via webhook
    """

    pi = stripe.PaymentIntent.retrieve(transaction_id)
    logger.info("INSIDE stripe_desync_check")
    logger.info(f"{pi = }")
    logger.info(f"{pi.status = }")
    if pi.status == "succeeded":
        logger.info(f"pi status succeeded")
        try:
            desynced_transaction = Transaction.objects.get(
                transaction_id=pi.id,
                is_succeeded=False
            )
            logger.info(f"{desynced_transaction = }")
        except Transaction.DoesNotExist:
            return
        else:
            with transaction.atomic():
                try:
                    logger.info(f"DB transaction started")
                    ds_pi = dsPaymentIntent.objects.get(id=pi.id)
                    logger.info(f"{ds_pi = }")
                except dsPaymentIntent.DoesNotExist:
                    ds_pi = dsPaymentIntent.objects.create(
                        **pi
                    )
                add_money_to_bank_account(
                    payment_intent=ds_pi,
                    cur_transaction=desynced_transaction
                )
                desynced_transaction.is_succeeded = True
                desynced_transaction.save()


def set_pay_for_tack_id(transaction_id, tack: Tack):
    """Setting up Tack into Transaction for subsequent Statistics collection"""

    if transaction_id:
        try:
            tr = Transaction.objects.get(transaction_id=transaction_id)
        except Transaction.DoesNotExist:
            pass
        else:
            tr.paid_tack = tack
            tr.save()
