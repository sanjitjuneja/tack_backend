from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.choices import TackStatus
from group.models import GroupTacks
from tack.models import Offer, Tack
from .tasks import delete_offer_task


@receiver(signal=post_save, sender=Offer)
def run_delete_offer_task(instance: Offer, created: bool, *args, **kwargs):
    if created:
        task = delete_offer_task.apply_async(
            countdown=instance.lifetime_seconds,
            kwargs={"offer_id": instance.id}
        )


# @receiver(signal=post_save, sender=Tack)
# def assign_tack_with_group(instance: Tack, created: bool, *args, **kwargs):
#     if created:
#         GroupTacks.objects.create(group=instance.tacker.active_group, tack=instance)
#
#
# @receiver(signal=post_delete, sender=Tack)
# def unassign_tack_with_group(instance: Tack, *args, **kwargs):
#     try:
#         gt = GroupTacks.objects.get(tack=instance)
#         gt.delete()
#     except ObjectDoesNotExist:
#         pass


@receiver(signal=post_save, sender=Offer)
def tack_status_on_offer_save(instance: Offer, *args, **kwargs):
    if Offer.objects.filter(tack=instance.tack).count() == 1:
        instance.tack.change_status(TackStatus.active)


@receiver(signal=post_delete, sender=Offer)
def tack_status_on_offer_delete(instance: Offer, *args, **kwargs):
    if Offer.objects.filter(tack=instance.tack).count() == 0:
        instance.tack.change_status(TackStatus.created)
