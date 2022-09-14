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
from tackapp.websocket_messages import WSSender

ws_sender = WSSender()
logger = logging.getLogger()
logger.warning(f"in Tack signals {ws_sender = }")


@receiver(signal=post_save, sender=Offer)
def run_delete_offer_task(instance: Offer, created: bool, *args, **kwargs):
    if created:
        task = delete_offer_task.apply_async(
            countdown=instance.lifetime_seconds,
            kwargs={"offer_id": instance.id}
        )
        logging.getLogger().info(task)


@receiver(signal=post_save, sender=Offer)
def tack_status_on_offer_save(instance: Offer, *args, **kwargs):
    if not instance.is_accepted:
        related_offers = Offer.active.filter(
            tack=instance.tack)
        if related_offers.count() == 1:
            instance.tack.change_status(TackStatus.ACTIVE)
        if related_offers.count() == 0:
            instance.tack.change_status(TackStatus.CREATED)


@receiver(signal=post_save, sender=Offer)
def send_websocket_message_on_offer_save(instance: Offer, *args, **kwargs):
    if instance.is_active:
        ws_sender.send_message(
            f"tack_{instance.tack.id}_tacker",
            'offer.create',
            OfferSerializer(instance).data)
        ws_sender.send_message(
            f"user_{instance.runner.id}",
            'runnertack.create',
            TacksOffersSerializer(instance).data)
    else:
        ws_sender.send_message(
            f"tack_{instance.tack.id}_tacker",
            'offer.delete',
            instance.id)
        ws_sender.send_message(
            f"user_{instance.runner.id}",
            'runnertack.delete',
            instance.id)


@receiver(signal=post_save, sender=Tack)
def tack_post_save(instance: Tack, created: bool, *args, **kwargs):
    if not instance.is_active:
        # Tack deletion process
        logging.getLogger().warning(f"if not instance.is_active:")
        ws_sender.send_message(
            f"tack_{instance.id}_tacker",
            'tack.delete',
            instance.id)
        ws_sender.send_message(
            f"tack_{instance.id}_offer",
            'runnertack.delete',
            instance.id)
        ws_sender.send_message(
            f"group_{instance.group.id}",
            'grouptack.delete',
            instance.id)
    else:
        if created:
            logging.getLogger().warning(f"Tack created")
            tack_serializer = TackDetailSerializer(instance)

            # Workaround on a problem to fly-calculate data for every User of the Group
            # This message model is GroupTackSerializer with hard-coded is_mine_offer_sent field
            message = {
                        'id': instance.id,
                        'tack': tack_serializer.data,
                        'is_mine_offer_sent': False
                      }
            ws_sender.send_message(
                f"group_{instance.group.id}",
                'grouptack.create',
                message)
            ws_sender.send_message(
                f"user_{instance.tacker.id}",
                'tack.create',
                tack_serializer.data)
        elif instance.status in (TackStatus.CREATED, TackStatus.ACTIVE):
            tack_serializer = TackDetailSerializer(instance)
            logging.getLogger().warning(f"if instance.status in (TackStatus.CREATED, TackStatus.ACTIVE):")
            message = {
                'id': instance.id,
                'tack': tack_serializer.data,
                'is_mine_offer_sent': False
            }
            ws_sender.send_message(
                f"group_{instance.group.id}",
                'grouptack.update',
                message)
            ws_sender.send_message(
                f"user_{instance.tacker.id}",
                'tack.update',
                tack_serializer.data)
        else:
            # Tack status changes for Tacker and Runner
            logging.getLogger().warning(f"else:")
            ws_sender.send_message(
                f"tack_{instance.tacker.id}_tacker",
                'tack.update',
                TackDetailSerializer(instance).data)
            ws_sender.send_message(
                f"tack_{instance.runner.id}_runner",
                'runnertack.update',
                TacksOffersSerializer(instance.accepted_offer).data)
