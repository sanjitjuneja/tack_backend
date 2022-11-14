import logging

from fcm_django.models import FCMDevice

from core.choices import TackStatus, OfferStatus, NotificationType, OfferType
from group.models import GroupMembers
from tackapp.websocket_messages import WSSender
from .models import Offer, Tack
from .notification import build_ntf_message
from .tasks import tack_long_inactive, tack_will_expire_soon


logger = logging.getLogger("debug")
ws_sender = WSSender()


def delete_tack_offers(tack: Tack):
    """Deleting all Offers related to Tack (On Tack delete)"""

    deleted_offers = Offer.active.filter(
        tack=tack
    )
    for offer in deleted_offers:
        logger.debug(f"{offer = }")
        ws_sender.send_message(
            f"user_{offer.tack.tacker_id}",  # tack_id_tacker
            'offer.delete',
            offer.id)
        ws_sender.send_message(
            f"user_{offer.runner_id}",  # tack_id_runner
            'runnertack.delete',
            offer.id)
    deleted_offers.update(
        status=OfferStatus.DELETED,
        is_active=False
    )


def deactivate_related_offers(tack: Tack):
    Offer.active.filter(tack=tack).update(is_active=False)


def calculate_tack_expiring(estimation_time_seconds: int) -> int:
    """Return a number of seconds when we need to send notification about soon Tack expiration"""

    return int(estimation_time_seconds * 0.9)


def notification_on_tack_created(tack: Tack):  # TACK_CREATED
    if not tack.tacker:
        return
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
    if not tack.tacker:
        return
    logger.debug(f"INSIDE deferred_notification_tack_inactive")
    tack_without_offer_seconds = 900
    tack_long_inactive.apply_async(
        countdown=tack_without_offer_seconds,
        kwargs={
            "tack_id": tack.id
        }
    )


def notification_on_tack_cancelled(tack: Tack):  # TACK_CANCELLED
    if not tack.tacker:
        return
    message = build_ntf_message(NotificationType.TACK_CANCELLED, tack)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)


def notification_on_tack_accepted(tack: Tack):  # TACK_ACCEPTED
    if not tack.tacker or not tack.runner:
        return
    message = build_ntf_message(NotificationType.TACK_ACCEPTED, tack)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)

    
def notification_on_tack_in_progress(tack: Tack):  # TACK_IN_PROGRESS
    if not tack.tacker or not tack.runner:
        return
    message = build_ntf_message(NotificationType.TACK_IN_PROGRESS, tack)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    
    
def notification_on_tack_waiting_review(tack: Tack):  # TACK_WAITING_REVIEW
    if not tack.tacker or not tack.runner:
        return
    message = build_ntf_message(NotificationType.TACK_WAITING_REVIEW, tack)
    FCMDevice.objects.filter(
        user_id=tack.runner_id
    ).send_message(message)
    
    
def notification_on_tack_finished(tack: Tack):  # TACK_FINISHED
    if not tack.tacker or not tack.runner:
        return
    message = build_ntf_message(NotificationType.TACK_FINISHED, tack)
    FCMDevice.objects.filter(
        user_id=tack.runner_id
    ).send_message(message)


def notification_on_offer_created(offer: Offer):
    if not offer.runner or not offer.tack.tacker:
        return
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
    if not offer.runner or not offer.tack.tacker:
        return
    message = build_ntf_message(NotificationType.OFFER_ACCEPTED, offer)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)


def deferred_notification_tack_will_expire_soon(offer: Offer):  # TACK_EXPIRING
    if not offer.runner or not offer.tack.tacker:
        return
    if not offer.tack.estimation_time_seconds:
        return
    tack_will_expire_soon.apply_async(
        countdown=calculate_tack_expiring(offer.tack.estimation_time_seconds),
        kwargs={
            "offer_id": offer.id
        }
    )


def notification_on_offer_expired(offer: Offer):  # OFFER_EXPIRED
    if not offer.runner or not offer.tack.tacker:
        return
    message = build_ntf_message(NotificationType.OFFER_EXPIRED, offer)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)


def notification_on_offer_finished(offer: Offer):  # RUNNER_FINISHED
    if not offer.runner or not offer.tack.tacker:
        return
    message = build_ntf_message(NotificationType.RUNNER_FINISHED, offer)
    FCMDevice.objects.filter(
        user_id=offer.tack.tacker_id
    ).send_message(message)
