from celery import shared_task
from django.db import transaction

from tack.models import Tack
from core.choices import TackStatus


@shared_task
@transaction.atomic
def change_tack_status(tack_id: int):
    tack = Tack.objects.get(pk=tack_id)
    tack.status = TackStatus.finished
    tack.save()
    return True
