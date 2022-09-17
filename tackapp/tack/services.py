from django.db import transaction
from django.utils import timezone

from core.choices import TackStatus, OfferStatus
from payment.services import send_payment_to_runner
from .models import Offer, Tack


@transaction.atomic
def accept_offer(offer: Offer):
    price = offer.price if offer.price else offer.tack.price
    delete_other_tack_offers(offer)
    offer.tack.runner = offer.runner
    offer.tack.accepted_offer = offer
    offer.tack.status = TackStatus.ACCEPTED
    offer.tack.accepted_time = timezone.now()
    offer.tack.price = price
    offer.status = OfferStatus.ACCEPTED
    offer.tack.tacker.bankaccount.usd_balance -= price
    offer.tack.tacker.bankaccount.save()
    offer.save()
    offer.tack.save()


def delete_other_tack_offers(offer: Offer):
    Offer.active.filter(
        tack=offer.tack
    ).exclude(
        id=offer.id
    ).update(
        status=OfferStatus.DELETED,
        is_active=False
    )


@transaction.atomic
def complete_tack(tack: Tack, message: str = None):
    tack.completion_message = message
    tack.completion_time = timezone.now()
    tack.status = TackStatus.WAITING_REVIEW
    tack.accepted_offer.status = OfferStatus.FINISHED
    tack.accepted_offer.save()
    tack.save()


@transaction.atomic
def confirm_complete_tack(tack: Tack):
    tack.completion_time = timezone.now()
    send_payment_to_runner(tack)
    tack.status = TackStatus.FINISHED
    tack.tacker.tacks_amount += 1
    tack.runner.tacks_amount += 1
    tack.tacker.save()
    tack.runner.save()
    tack.save()


def deactivate_related_offers(tack: Tack):
    Offer.active.filter(tack=tack).update(is_active=False)


def calculate_tack_expiring(estimation_time_seconds: int) -> int:
    return int(estimation_time_seconds * 0.9)
