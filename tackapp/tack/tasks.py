from celery import shared_task
from django.db import transaction

from tack.models import Tack, Offer
from core.choices import TackStatus


@shared_task
@transaction.atomic
def change_tack_status(tack_id: int):
    tack = Tack.objects.get(pk=tack_id)
    tack.status = TackStatus.finished
    tack.save()
    return True


@shared_task
@transaction.atomic
def delete_offer_task(offer_id: int):
    offer = Offer.objects.get(pk=offer_id)
    offer.delete()
    return True
