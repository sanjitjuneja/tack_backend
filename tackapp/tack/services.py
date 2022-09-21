import logging
import sys

from django.db import transaction
from django.db.models import Subquery
from django.utils import timezone
from fcm_django.models import FCMDevice

from core.choices import TackStatus, OfferStatus, NotificationType, OfferType
from group.models import GroupMembers
from payment.services import send_payment_to_runner
from .models import Offer, Tack
from .notification import build_ntf_message, get_message_template
from .tasks import tack_long_inactive, tack_will_expire_soon


logger = logging.getLogger("myproject.custom")
# logger.setLevel("INFO")
# sh = logging.StreamHandler(sys.stdout)
# logger.addHandler(sh)


@transaction.atomic
def accept_offer(offer: Offer):
    price = offer.price if offer.price else offer.tack.price
    offer.tack.runner = offer.runner
    offer.tack.accepted_offer = offer
    offer.tack.status = TackStatus.ACCEPTED
    offer.tack.accepted_time = timezone.now()
    offer.tack.price = price
    offer.tack.save()

    delete_other_tack_offers(offer)
    offer.status = OfferStatus.ACCEPTED
    offer.save()

    offer.tack.tacker.bankaccount.usd_balance -= price
    offer.tack.tacker.bankaccount.save()


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
    tack.save()

    tack.accepted_offer.status = OfferStatus.FINISHED
    tack.accepted_offer.save()


@transaction.atomic
def confirm_complete_tack(tack: Tack):
    send_payment_to_runner(tack)
    tack.status = TackStatus.FINISHED
    tack.tacker.tacks_amount += 1
    tack.runner.tacks_amount += 1
    tack.save()
    tack.tacker.save()
    tack.runner.save()


def deactivate_related_offers(tack: Tack):
    Offer.active.filter(tack=tack).update(is_active=False)


def calculate_tack_expiring(estimation_time_seconds: int) -> int:
    return int(estimation_time_seconds * 0.9)


def notification_on_tack_created(tack: Tack):  # TACK_CREATED
    message = build_ntf_message(NotificationType.TACK_CREATED, tack)
    not_muted_members = GroupMembers.objects.filter(
        group=tack.group_id,
        is_muted=False
    ).exclude(
        member=tack.tacker_id
    ).values_list(
        "member",
        flat=True
    )
    FCMDevice.objects.filter(
        user__in=not_muted_members
    ).send_message(message)


def deferred_notification_tack_inactive(tack: Tack):  # TACK_INACTIVE
    logger.warning(f"INSIDE deferred_notification_tack_inactive")
    tack_without_offer_seconds = 900
    tack_long_inactive.apply_async(
        countdown=tack_without_offer_seconds,
        kwargs={
            "tack_id": tack.id
        }
    )


def notification_on_tack_cancelled(tack: Tack):  # TACK_CANCELLED
    message = build_ntf_message(NotificationType.TACK_CANCELLED, tack)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)


def notification_on_tack_accepted(tack: Tack):  # TACK_ACCEPTED
    message = build_ntf_message(NotificationType.TACK_ACCEPTED, tack)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)

    
def notification_on_tack_in_progress(tack: Tack):  # TACK_IN_PROGRESS
    message = build_ntf_message(NotificationType.TACK_IN_PROGRESS, tack)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    
    
def notification_on_tack_waiting_review(tack: Tack):  # RUNNER_FINISHED
    message = build_ntf_message(NotificationType.RUNNER_FINISHED, tack)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    
    
def notification_on_tack_finished(tack: Tack):  # TACK_FINISHED
    message = build_ntf_message(NotificationType.TACK_FINISHED, tack)
    FCMDevice.objects.filter(
        user_id=tack.runner_id
    ).send_message(message)


def notification_on_offer_created(offer: Offer):
    match offer.offer_type:
        case OfferType.OFFER:  # OFFER_RECEIVED
            ntf_type = NotificationType.OFFER_RECEIVED
        case OfferType.COUNTER_OFFER:  # COUNTEROFFER_RECEIVED
            ntf_type = NotificationType.COUNTEROFFER_RECEIVED
        case _:
            return
    message = build_ntf_message(ntf_type, offer)
    FCMDevice.objects.filter(
        user_id=offer.tack.tacker_id
    ).send_message(message)


def notification_on_offer_accepted(offer: Offer):  # OFFER_ACCEPTED
    message = build_ntf_message(NotificationType.OFFER_ACCEPTED, offer)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)


def deferred_notification_tack_will_expire_soon(offer: Offer):  # TACK_EXPIRING
    if not offer.tack.estimation_time_seconds:
        return
    tack_will_expire_soon.apply_async(
        countdown=calculate_tack_expiring(offer.tack.estimation_time_seconds),
        kwargs={
            "offer_id": offer.id
        }
    )


def notification_on_offer_expired(offer: Offer):  # OFFER_EXPIRED
    message = build_ntf_message(NotificationType.OFFER_EXPIRED, offer)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)


def notification_on_offer_finished(offer: Offer):  # RUNNER_FINISHED
    message = build_ntf_message(NotificationType.RUNNER_FINISHED, offer)
    FCMDevice.objects.filter(
        user_id=offer.tack.tacker_id
    ).send_message(message)
