import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.choices import TackStatus
from group.models import GroupTacks
from tack.models import Offer, Tack
from user.models import User
from .serializers import TackDetailSerializer
from .tasks import delete_offer_task


@receiver(signal=post_save, sender=Offer)
def run_delete_offer_task(instance: Offer, created: bool, *args, **kwargs):
    if created:
        task = delete_offer_task.apply_async(
            countdown=instance.lifetime_seconds,
            kwargs={"offer_id": instance.id}
        )


@receiver(signal=post_save, sender=Offer)
def tack_status_on_offer_save(instance: Offer, *args, **kwargs):
    if not instance.is_accepted:
        if Offer.active.filter(tack=instance.tack).count() == 1:
            instance.tack.change_status(TackStatus.ACTIVE)


@receiver(signal=post_delete, sender=Offer)
def tack_status_on_offer_delete(instance: Offer, *args, **kwargs):
    if Offer.active.filter(tack=instance.tack).count() == 0:
        instance.tack.change_status(TackStatus.CREATED)


@receiver(signal=post_save, sender=Tack)
def tack_post_save(instance: Tack, created: bool, *args, **kwargs):
    channel_layer = get_channel_layer()
    logging.getLogger().warning(f"in signal: {channel_layer.__dict__ = }")

    # tacks = Tack.active.filter(
    #     group=instance.group,
    #     status__in=(TackStatus.CREATED, TackStatus.ACTIVE),
    # ).prefetch_related(
    #     Prefetch("user_set", queryset=User.objects.filter(groupmembers=instance.group))
    # ).select_related(
    #     "tacker",
    #     "runner",
    #     "group",
    # ).order_by(
    #     "creation_time"
    # )

    async_to_sync(channel_layer.group_send)(
        f"group_{instance.group}",
        {
            'type': 'tack.create',
            'message': TackDetailSerializer(instance).data
        })
