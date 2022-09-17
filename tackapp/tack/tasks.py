from datetime import timedelta

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Subquery
from django.utils import timezone

from payment.services import send_payment_to_runner
from tack.models import Tack, Offer
from core.choices import TackStatus, OfferStatus
from user.models import User

from fcm_django.models import FCMDevice
from .notification import create_message, send_message


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
def tack_long_inactive(tack_id, user_id, data, nf_types) -> None:
    # if this tack already had offers - do not send notification
    if Offer.objects.filter(tack=tack_id).exists():
        return
    # if this tack is not in active objects(deleted) - do not send notification
    try:
        if Tack.active.get(id=tack_id):
            return
    except Tack.DoesNotExist:
        return
    messages = create_message(data, nf_types)
    devices = FCMDevice.objects.filter(user=user_id)
    send_message(messages, (devices,))


@shared_task
def tack_expire_soon(user_id, data, nf_types) -> None:
    messages = create_message(data, nf_types)
    devices = FCMDevice.objects.filter(user=user_id)
    send_message(messages, (devices,))
