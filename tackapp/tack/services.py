import logging
import sys

from django.db import transaction
from django.db.models import Subquery
from django.utils import timezone
from fcm_django.models import FCMDevice

from core.choices import TackStatus, OfferStatus
from group.models import GroupMembers
from payment.services import send_payment_to_runner
from .models import Offer, Tack
from .notification import build_ntf_message, build_title_body_from_tack, build_title_body_from_offer, \
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


def notification_on_tack_created(tack: Tack):
    ntf_title, ntf_body, ntf_image_url = build_title_body_from_tack("tack_created", tack)
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


def deferred_notification_tack_inactive(tack: Tack):
    logger.warning(f"INSIDE deferred_notification_tack_inactive")
    tack_without_offer_seconds = 5
    tack_long_inactive.apply_async(
        countdown=tack_without_offer_seconds,
        kwargs={
            "tack_id": tack.id
        }
    )


def notification_on_tack_cancelled(tack: Tack):
    ntf_title, ntf_body, ntf_image_url = build_title_body_from_tack("canceled", tack)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.tacker}")

    
def notification_on_tack_in_progress(tack: Tack):
    ntf_title, ntf_body, ntf_image_url = build_title_body_from_tack("in_progress", tack)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.tacker}")
    
    
def notification_on_tack_waiting_review(tack: Tack):
    ntf_title, ntf_body, ntf_image_url = build_title_body_from_tack("waiting_review", tack)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.tacker}")
    
    
def notification_on_tack_finished(tack: Tack):
    ntf_title, ntf_body, ntf_image_url = build_title_body_from_tack("finished", tack)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=tack.runner_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {tack.runner}")


def notification_on_offer_created(offer: Offer):
    ntf_title, ntf_body, ntf_image_url = build_title_body_from_offer("offer_received", offer)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=offer.tack.tacker_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {offer.tack.tacker}")


def notification_on_offer_accepted(offer: Offer):
    ntf_title, ntf_body, ntf_image_url = build_title_body_from_offer("offer_accepted", offer)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {offer.runner}")


def deferred_notification_tack_will_expire_soon(offer: Offer):
    if not offer.tack.estimation_time_seconds:
        return
    tack_will_expire_soon.apply_async(
        countdown=calculate_tack_expiring(offer.tack.estimation_time_seconds),
        kwargs={
            "offer_id": offer.id
        }
    )


def notification_on_offer_expired(offer: Offer):
    ntf_title, ntf_body, ntf_image_url = build_title_body_from_offer("offer_expired", offer)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)
    logger.info(f"Sent [{formatted_ntf_title} : {formatted_ntf_body} : {ntf_image_url}] to {offer.runner}")
