from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from payment.services import send_payment_to_runner
from tack.models import Tack, Offer
from core.choices import TackStatus


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
def delete_offer_task(offer_id: int):
    try:
        offer = Offer.objects.get(pk=offer_id)
    except ObjectDoesNotExist:
        return False

    offer.is_active = False
    offer.save()
