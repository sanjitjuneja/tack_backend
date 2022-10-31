import logging

from django.db import transaction, IntegrityError
from django.utils import timezone
from fcm_django.models import FCMDevice

from core.choices import TackStatus, OfferStatus, NotificationType, OfferType
from group.models import GroupMembers
from payment.services import send_payment_to_runner
from tackapp.websocket_messages import WSSender
from .models import Offer, Tack
from .notification import build_ntf_message
from .tasks import tack_long_inactive, tack_will_expire_soon


logger = logging.getLogger("debug")
ws_sender = WSSender()


@transaction.atomic
def accept_offer(offer: Offer):
    delete_other_tack_offers(offer)
    offer.status = OfferStatus.ACCEPTED
    offer.save()

    price = offer.price if offer.price else offer.tack.price
    offer.tack.runner = offer.runner
    offer.tack.accepted_offer = offer
    offer.tack.status = TackStatus.ACCEPTED
    offer.tack.accepted_time = timezone.now()
    offer.tack.price = price
    offer.tack.save()

    if not offer.tack.auto_accept:
        offer.tack.tacker.bankaccount.usd_balance -= price
    offer.tack.tacker.bankaccount.save()


def delete_other_tack_offers(offer: Offer):
    other_offers = Offer.active.filter(
        tack=offer.tack
    ).exclude(
        id=offer.id
    )
    for offer in other_offers:
        logger.debug(f"{offer = }")
        ws_sender.send_message(
            f"user_{offer.tack.tacker_id}",  # tack_id_tacker
            'offer.delete',
            offer.id)
        ws_sender.send_message(
            f"user_{offer.runner_id}",  # tack_id_runner
            'runnertack.delete',
            offer.id)
    other_offers.update(
        status=OfferStatus.DELETED,
        is_active=False
    )


def delete_tack_offers(tack: Tack):
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


@transaction.atomic
def complete_tack(tack: Tack, message: str = None):
    tack.completion_message = message
    tack.completion_time = timezone.now()
    tack.status = TackStatus.WAITING_REVIEW
    tack.save()

    tack.accepted_offer.status = OfferStatus.FINISHED
    tack.accepted_offer.save()


def confirm_complete_tack(tack: Tack):
    try:
        with transaction.atomic():
            tack.status = TackStatus.FINISHED
            tack.tacker.tacks_amount += 1
            tack.runner.tacks_amount += 1
            tack.is_paid = send_payment_to_runner(tack)
            tack.tacker.save()
            tack.runner.save()
            tack.save()
    except IntegrityError as e:
        logger.error(f"tack.services.confirm_complete_tack {e = }")


def deactivate_related_offers(tack: Tack):
    Offer.active.filter(tack=tack).update(is_active=False)


def calculate_tack_expiring(estimation_time_seconds: int) -> int:
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
