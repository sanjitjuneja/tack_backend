import logging
from datetime import timedelta

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Subquery
from django.utils import timezone

from payment.services import send_payment_to_runner
from tack.models import Tack, Offer
from core.choices import TackStatus, OfferStatus, NotificationType
from tack.notification import build_title_body, build_ntf_message, \
    get_formatted_ntf_title_body_from_tack, get_formatted_ntf_title_body_from_offer
from user.models import User

from fcm_django.models import FCMDevice


logger_services = logging.getLogger("tack.services")


@shared_task
@transaction.atomic
def change_tack_status_finished(tack_id: int):
    tack = Tack.objects.get(pk=tack_id)
    if tack.status != TackStatus.FINISHED:
        send_payment_to_runner(tack)
        tack.status = TackStatus.FINISHED
        tack.tacker.tacks_amount += 1
        tack.runner.tacks_amount += 1
        tack.tacker.save()
        tack.runner.save()
        tack.save()


@shared_task
@transaction.atomic
def set_expire_offer_task(offer_id: int) -> None:
    try:
        offer = Offer.objects.get(pk=offer_id)
    except ObjectDoesNotExist:
        return None
    if offer.status == OfferStatus.CREATED:
        offer.set_expired_status()


@shared_task
def set_tack_inactive_on_user_last_login() -> None:
    Tack.objects.filter(
        tacker__in=Subquery(
            User.objects.filter(
                last_login__gt=timezone.now() - timedelta(days=1)
            )
        )
    ).update(is_active=False)


@shared_task
def set_tack_active_on_user_last_login(user_id: int) -> None:
    Tack.objects.filter(tacker=user_id).update(is_active=True)


@shared_task
def tack_long_inactive(tack_id) -> None:
    # if this tack already had offers - do not send notification
    logger_services.warning("INSIDE tack_long_inactive")
    if Offer.objects.filter(tack=tack_id).exists():
        return
    # if this tack is not in active objects(deleted) - do not send notification
    try:
        if tack := Tack.active.get(id=tack_id):
            if tack.status != TackStatus.CREATED:
                return
            ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.TACK_INACTIVE)
            formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_tack(ntf_title, ntf_body, tack)
            message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
            FCMDevice.objects.filter(
                user_id=tack.tacker_id
            ).send_message(message)
            logger_services.info(f"Sent [{ntf_title} : {ntf_body} :{ntf_image_url}] to {tack.tacker}")
    except Tack.DoesNotExist:
        return


@shared_task
def tack_will_expire_soon(offer_id) -> None:
    try:
        offer = Offer.active.get(id=offer_id)
    except Offer.DoesNotExist:
        return
    if offer.status != OfferStatus.IN_PROGRESS:
        return
    ntf_title, ntf_body, ntf_image_url = build_title_body(NotificationType.TACK_EXPIRING)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_body_from_offer(ntf_title, ntf_body, offer)
    message = build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)
    logger_services.info(f"Sent [{ntf_title} : {ntf_body} : {ntf_image_url}] to {offer.runner}")
