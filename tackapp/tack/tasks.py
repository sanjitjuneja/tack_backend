from datetime import timedelta

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Subquery
from django.utils import timezone

from payment.services import send_payment_to_runner
from tack.models import Tack, Offer
from core.choices import TackStatus
from user.models import User


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
def delete_offer_task(offer_id: int) -> None:
    try:
        offer = Offer.objects.get(pk=offer_id)
    except ObjectDoesNotExist:
        return None
    if not offer.is_accepted:
        offer.is_active = False
        offer.save()


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
