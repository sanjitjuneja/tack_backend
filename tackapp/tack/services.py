import logging
import sys

from django.db import transaction
from django.db.models import Subquery
from django.utils import timezone
from fcm_django.models import FCMDevice

from core.choices import TackStatus, OfferStatus, NotificationType
from group.models import GroupMembers
from payment.services import send_payment_to_runner
from .models import Offer, Tack
from .notification import build_ntf_message, build_title_body, \
    get_formatted_ntf_title_body_from_tack, get_formatted_ntf_title_body_from_offer
from .tasks import tack_long_inactive, tack_will_expire_soon


logger = logging.getLogger("myproject.custom")
# logger.setLevel("INFO")
# sh = logging.StreamHandler(sys.stdout)
# logger.addHandler(sh)


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


def notification_on_tack_created(tack: Tack):  # TACK_CREATED
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.TACK_CREATED)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
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
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {not_muted_members}")


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
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.TACK_CANCELLED)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.tacker}")


def notification_on_tack_accepted(tack: Tack):  # TACK_ACCEPTED
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.TACK_ACCEPTED)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.tacker}")

    
def notification_on_tack_in_progress(tack: Tack):  # TACK_IN_PROGRESS
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.TACK_IN_PROGRESS)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.tacker}")
    
    
def notification_on_tack_waiting_review(tack: Tack):  # RUNNER_FINISHED
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.RUNNER_FINISHED)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.tacker}")
    
    
def notification_on_tack_finished(tack: Tack):  # TACK_FINISHED
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.TACK_FINISHED)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.runner_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.runner}")


def notification_on_offer_created(offer: Offer):  # OFFER_RECEIVED
    if offer.price:
        ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.COUNTEROFFER_RECEIVED)
        formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
        message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
        FCMDevice.objects.filter(
            user_id=offer.tack.tacker_id
        ).send_message(message)
        logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {offer.tack.tacker}")
    else:  # COUNTEROFFER_RECEIVED
        ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.OFFER_RECEIVED)
        formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
        message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
        FCMDevice.objects.filter(
            user_id=offer.tack.tacker_id
        ).send_message(message)
        logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {offer.tack.tacker}")


def notification_on_offer_accepted(offer: Offer):  # OFFER_ACCEPTED
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.OFFER_ACCEPTED)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {offer.runner}")


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
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.OFFER_EXPIRED)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {offer.runner}")


def notification_on_offer_finished(offer: Offer):  # RUNNER_FINISHED
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.RUNNER_FINISHED)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=offer.tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {offer.runner}")
