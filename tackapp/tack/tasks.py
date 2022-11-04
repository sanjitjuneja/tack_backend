import logging
from datetime import timedelta

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Subquery, Max, Value, Q
from django.utils import timezone

from payment.services import send_payment_to_runner
from tack.models import Tack, Offer
from core.choices import TackStatus, OfferStatus, NotificationType
from tack.notification import build_ntf_message
from tackapp.websocket_messages import WSSender
from user.models import User

from fcm_django.models import FCMDevice


logger = logging.getLogger("debug")
ws_sender = WSSender()


@shared_task
@transaction.atomic
def change_tack_status_finished(tack_id: int):
    logger.debug(f"change_tack_status_finished {tack_id = }")
    tack = Tack.objects.get(pk=tack_id)
    logger.debug(f"change_tack_status_finished {tack = }")
    if tack.status != TackStatus.FINISHED:
        logger.debug("inside if stmt of change_tack_status_finished")
        tack.is_paid = send_payment_to_runner(tack)
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
def tack_long_inactive(tack_id) -> None:
    # if this tack already had offers - do not send notification
    logger.debug("tack.tasks.tack_long_inactive")
    if Offer.objects.filter(tack=tack_id).exists():
        return
    # if this tack is not in active objects(deleted) - do not send notification
    try:
        if tack := Tack.active.get(id=tack_id):
            if tack.status != TackStatus.CREATED:
                return
            message = build_ntf_message(NotificationType.TACK_INACTIVE, tack)
            FCMDevice.objects.filter(
                user_id=tack.tacker_id
            ).send_message(message)
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
    message = build_ntf_message(NotificationType.TACK_EXPIRING, offer)
    FCMDevice.objects.filter(
        user_id=offer.runner_id
    ).send_message(message)


@shared_task
def delete_inactive_tacks():
    """Task for soft-deleting Tacks that have not received Offers for 2 days"""

    del_tacks = Tack.active.filter(
        status=TackStatus.CREATED,
        creation_time__lte=timezone.now() - timedelta(days=2)
    ).annotate(
        max_offer_creation_time=Max('offer__creation_time')
    ).filter(
        Q(max_offer_creation_time__isnull=True) |
        Q(max_offer_creation_time__lte=timezone.now() - timedelta(days=2))
    )
    for tack in del_tacks:
        ws_sender.send_message(
            f"user_{tack.tacker_id}",
            "tack.delete",
            tack.id
        )
        ws_sender.send_message(
            f"group_{tack.group_id}",
            "grouptack.delete",
            tack.id
        )
    del_tacks.update(
        is_active=False
    )
