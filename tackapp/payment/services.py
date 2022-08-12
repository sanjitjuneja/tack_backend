from django.db import transaction

from core.choices import OfferType
from tack.models import Tack


@transaction.atomic
def send_payment_to_runner(tack: Tack):
    if tack.is_paid:
        return
    if tack.accepted_offer.offer_type == OfferType.OFFER:
        tack.runner.bankaccount.usd_balance += tack.price
        tack.is_paid = True
        tack.save()
    elif tack.accepted_offer.offer_type == OfferType.COUNTER_OFFER:
        tack.runner.bankaccount.usd_balance += tack.accepted_offer.price
        tack.is_paid = True
        tack.save()
