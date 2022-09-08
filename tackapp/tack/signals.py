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
from .serializers import TackDetailSerializer, OfferSerializer, TacksOffersSerializer
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


@receiver(signal=post_save, sender=Offer)
def send_websocket_message_on_offer_save(instance: Offer, *args, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"tack_{instance.tack.id}_tacker",
        {
            'type': 'offer.create',
            'message': OfferSerializer(instance).data
        })

    instance = Offer.active.get(
        pk=instance.id
    ).select_related(
        "tack",
        "tack__tacker",
        "runner",
        "tack__group"
    )
    async_to_sync(channel_layer.group_send)(
        f"tack_{instance.tack.id}_runner",
        {
            'type': 'runnertack.create',
            'message': TacksOffersSerializer(instance).data
        })


@receiver(signal=post_delete, sender=Offer)
def tack_status_on_offer_delete(instance: Offer, *args, **kwargs):
    if Offer.active.filter(tack=instance.tack).count() == 0:
        instance.tack.change_status(TackStatus.CREATED)


@receiver(signal=post_delete, sender=Offer)
def send_websocket_message_on_offer_delete(instance: Offer, *args, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"tack_{instance.tack.id}_tacker",
        {
            'type': 'offer.delete',
            'message': instance.id
        })
    async_to_sync(channel_layer.group_send)(
        f"tack_{instance.tack.id}_runner",
        {
            'type': 'runnertack.delete',
            'message': instance.id
        })


@receiver(signal=post_save, sender=Tack)
def tack_post_save(instance: Tack, created: bool, *args, **kwargs):
    channel_layer = get_channel_layer()

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

    # Workaround on a problem to fly-calculate data for every User of the Group
    # This message model is GroupTackSerializer with hard-coded is_mine_offer_sent field
    if created:
        logging.getLogger().warning(f"Tack created")
        async_to_sync(channel_layer.group_send)(
            f"group_{instance.group.id}",
            {
                'type': 'grouptack.create',
                'message': {
                    'id': instance.id,
                    'tack': TackDetailSerializer(instance).data,
                    'is_mine_offer_sent': False
                }
            })
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.tacker.id}",
            {
                'type': 'tack.create',
                'message': TackDetailSerializer(instance).data
            })


@receiver(signal=post_delete, sender=Tack)
def tack_post_delete(instance: Tack, created: bool, *args, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"tack_{instance.id}_tacker",
        {
            'type': 'tack.delete',
            'message': instance.id
        })
    async_to_sync(channel_layer.group_send)(
        f"tack_{instance.id}_offer",
        {
            'type': 'runnertack.delete',
            'message': instance.id
        })
    async_to_sync(channel_layer.group_send)(
        f"group_{instance.group.id}",
        {
            'type': 'grouptack.delete',
            'message': instance.id
        })
