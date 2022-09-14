from datetime import datetime

from django.db import transaction
from django.utils import timezone

from core.choices import TackStatus
from payment.services import send_payment_to_runner
from .models import Offer, Tack


TACK_WITHOUT_OFFER_TIME = 900


@transaction.atomic
def accept_offer(offer: Offer):
    offer.tack.runner = offer.runner
    offer.tack.accepted_offer = offer
    offer.tack.status = TackStatus.ACCEPTED
    offer.tack.accepted_time = timezone.now()
    offer.is_accepted = True
    offer.save()
    offer.tack.save()


@transaction.atomic
def complete_tack(tack: Tack, message: str):
    tack.completion_message = message
    tack.completion_time = timezone.now()
    tack.status = TackStatus.WAITING_REVIEW
    tack.save()


@transaction.atomic
def confirm_complete_tack(tack: Tack):
    tack.completion_time = timezone.now()
    send_payment_to_runner(tack)
    tack.status = TackStatus.FINISHED
    tack.save()


def deactivate_related_offers(tack: Tack):
    Offer.active.filter(tack=tack).update(is_active=False)


def calculate_tack_expiring(estimation_time_seconds: int) -> int:
    return int(estimation_time_seconds * 0.9)
