from celery import shared_task
from django.db import transaction

from payment.services import send_payment_to_runner
from tack.models import Tack, Offer
from core.choices import TackStatus


@shared_task
@transaction.atomic
def change_tack_status_finished(tack_id: int):
    tack = Tack.objects.get(pk=tack_id)
    if tack.status != TackStatus.finished:
        send_payment_to_runner(tack)
        tack.status = TackStatus.finished
        tack.tacker.tacks_amount += 1
        tack.runner.tacks_amount += 1
        tack.tacker.save()
        tack.runner.save()
        tack.save()
    return True


@shared_task
@transaction.atomic
def delete_offer_task(offer_id: int):
    offer = Offer.objects.get(pk=offer_id)
    offer.delete()
    return True
