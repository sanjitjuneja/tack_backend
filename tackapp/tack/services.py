from datetime import datetime

from django.db import transaction

from core.choices import TackStatus
from .models import Offer, Tack


@transaction.atomic
def accept_offer(offer: Offer):
    offer.tack.runner = offer.runner
    offer.tack.status = TackStatus.accepted
    offer.tack.price = offer.price if offer.price else offer.tack.price
    offer.is_accepted = True
    offer.save()
    offer.tack.save()


@transaction.atomic
def complete_tack(tack: Tack, message: str):
    tack.completion_message = message
    tack.completion_time = datetime.now()
    tack.change_status(TackStatus.waiting_review)
