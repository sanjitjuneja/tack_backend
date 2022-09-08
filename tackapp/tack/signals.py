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
    if instance.is_active:
        async_to_sync(channel_layer.group_send)(
            f"tack_{instance.tack.id}_tacker",
            {
                'type': 'offer.create',
                'message': OfferSerializer(instance).data
            })

        async_to_sync(channel_layer.group_send)(
            f"tack_{instance.tack.id}_runner",
            {
                'type': 'runnertack.create',
                'message': TacksOffersSerializer(instance).data
            })
    else:
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

    logging.getLogger().warning(f"in send_websocket_message_on_offer_save")


@receiver(signal=post_delete, sender=Offer)
def tack_status_on_offer_delete(instance: Offer, *args, **kwargs):
    if Offer.active.filter(tack=instance.tack).count() == 0:
        instance.tack.change_status(TackStatus.CREATED)


# @receiver(signal=post_delete, sender=Offer)
# def send_websocket_message_on_offer_delete(instance: Offer, *args, **kwargs):
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         f"tack_{instance.tack.id}_tacker",
#         {
#             'type': 'offer.delete',
#             'message': instance.id
#         })
#     async_to_sync(channel_layer.group_send)(
#         f"tack_{instance.tack.id}_runner",
#         {
#             'type': 'runnertack.delete',
#             'message': instance.id
#         })


@receiver(signal=post_save, sender=Tack)
def tack_post_save(instance: Tack, created: bool, *args, **kwargs):
    channel_layer = get_channel_layer()

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
    if not instance.is_active:
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
    if instance.status in (TackStatus.CREATED, TackStatus.ACTIVE):
        async_to_sync(channel_layer.group_send)(
            f"group_{instance.group.id}",
            {
                'type': 'grouptack.update',
                'message': {
                    'id': instance.id,
                    'tack': TackDetailSerializer(instance).data,
                    'is_mine_offer_sent': False
                }
            })
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.tacker.id}",
            {
                'type': 'tack.update',
                'message': TackDetailSerializer(instance).data
            })
    else:
        async_to_sync(channel_layer.group_send)(
            f"tack_{instance.id}_tacker",
            {
                'type': 'tack.update',
                'message': {
                    'id': instance.id,
                    'tack': TackDetailSerializer(instance).data,
                    'is_mine_offer_sent': False
                }
            })
        async_to_sync(channel_layer.group_send)(
            f"tack_{instance.id}_runner",
            {
                'type': 'runnertack.update',
                'message': TacksOffersSerializer(instance).data
            })
