from datetime import datetime

from django.db import transaction
from django.utils import timezone

from core.choices import TackStatus
from .models import Offer, Tack


@transaction.atomic
def accept_offer(offer: Offer):
    offer.tack.runner = offer.runner
    offer.tack.status = TackStatus.ACCEPTED
    offer.tack.price = offer.price if offer.price else offer.tack.price
    offer.tack.accepted_time = timezone.now()
    offer.is_accepted = True
    offer.save()
    offer.tack.save()


@transaction.atomic
def complete_tack(tack: Tack, message: str):
    tack.completion_message = message
    tack.completion_time = datetime.now()
    tack.status = TackStatus.WAITING_REVIEW
    tack.save()
