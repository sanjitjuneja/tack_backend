import logging

from django.db.models import Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.choices import OfferStatus
from group.models import GroupMembers
from tack.models import Offer, Tack
from tack.serializers import TackDetailSerializer, OfferSerializer, TacksOffersSerializer
from tackapp.websocket_messages import WSSender
from tack.tasks import delete_offer_task, tack_long_inactive, tack_expire_soon
from tack.services import TACK_WITHOUT_OFFER_TIME, calculate_tack_expiring
from tack.notification import create_message, send_message

from core.choices import TackStatus

from fcm_django.models import FCMDevice

ws_sender = WSSender()
logger = logging.getLogger()
logger.warning(f"in Tack signals {ws_sender = }")


@receiver(signal=post_save, sender=Offer)
def run_delete_offer_task(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"run_delete_offer_task. {instance.status = }")
    if created:
        task = delete_offer_task.apply_async(
            countdown=instance.lifetime_seconds,
            kwargs={"offer_id": instance.id}
        )
        logging.getLogger().info(f"run_delete_offer_task {task}")


@receiver(signal=post_save, sender=Offer)
def tack_status_on_offer_save(instance: Offer, *args, **kwargs):
    logger.warning(f"tack_status_on_offer_save. {instance.status = }")

    # TODO: rethink guard statement to 1 SQL query
    if instance.tack.status not in (TackStatus.CREATED, TackStatus.ACTIVE):
        return
    if instance.status in (OfferStatus.CREATED, OfferStatus.EXPIRED, OfferStatus.DELETED):
        related_offers = Offer.objects.filter(
            tack=instance.tack,
            status=OfferStatus.CREATED)
        if related_offers.count() == 1:
            instance.tack.change_status(TackStatus.ACTIVE)
        if related_offers.count() == 0:
            instance.tack.change_status(TackStatus.CREATED)


@receiver(signal=post_save, sender=Offer)
def offer_created(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"offer_created. {instance.status = }")
    if created and instance.status == OfferStatus.CREATED:
        logger.warning(f"if created:")
        tack_serializer = TackDetailSerializer(instance.tack)
        runner_message = {
            'id': instance.id,
            'tack': tack_serializer.data,
            'is_mine_offer_sent': True
        }
        ws_sender.send_message(
            f"user_{instance.tack.tacker_id}",  # tack_{instance.tack_id}_tacker
            'offer.create',
            OfferSerializer(instance).data)
        ws_sender.send_message(
            f"user_{instance.runner_id}",
            'runnertack.create',
            TacksOffersSerializer(instance).data)
        ws_sender.send_message(
            f"tack_{instance.id}_offer",
            "grouptack.update",
            runner_message
        )


@receiver(signal=post_save, sender = Offer)
def offer_expired(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"offer_expired. {instance.status = }")
    if not created and instance.status == OfferStatus.EXPIRED:
        ws_sender.send_message(
            f"user_{instance.tack.tacker_id}",  # tack_id_tacker
            'offer.delete',
            instance.id)
        ws_sender.send_message(
            f"user_{instance.runner_id}",  # tack_id_runner
            'runnertack.delete',
            instance.id)


@receiver(signal=post_save, sender=Offer)
def offer_accepted(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"offer_accepted. {instance.status = }")
    if not created and instance.status == OfferStatus.ACCEPTED:
        ws_sender.send_message(
            f"user_{instance.tack.tacker_id}",  # tack_{instance.tack_id}_tacker
            'tack.update',
            TackDetailSerializer(instance.tack).data)
        ws_sender.send_message(
            f"user_{instance.tack.runner_id}",  # tack_{instance.tack_id}_runner
            'runnertack.update',
            TacksOffersSerializer(instance).data)
        # is this needed?
        ws_sender.send_message(
            f"user_{instance.tack.tacker_id}",
            "offer.delete",
            instance.id)


@receiver(signal=post_save, sender=Offer)
def offer_in_progress(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"offer_in_progress. {instance.status = }")
    if not created and instance.status == OfferStatus.IN_PROGRESS:
        ws_sender.send_message(
            f"user_{instance.tack.tacker_id}",  # tack_{instance.tack_id}_tacker
            'tack.update',
            TackDetailSerializer(instance.tack).data)
        ws_sender.send_message(
            f"user_{instance.tack.runner_id}",  # tack_{instance.tack_id}_runner
            'runnertack.update',
            TacksOffersSerializer(instance).data)


@receiver(signal=post_save, sender=Offer)
def offer_finished(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"offer_finished. {instance.status = }")
    if not created and instance.status == OfferStatus.FINISHED:
        ws_sender.send_message(
            f"user_{instance.tack.tacker_id}",  # tack_id_tacker
            'offer.delete',
            instance.id)
        ws_sender.send_message(
            f"user_{instance.runner_id}",  # tack_id_runner
            'runnertack.delete',
            instance.id)


@receiver(signal=post_save, sender=Offer)
def offer_deleted(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"offer_deleted. {instance.status = }")
    if not created and instance.status == OfferStatus.DELETED:
        ws_sender.send_message(
            f"user_{instance.tack.tacker_id}",  # tack_id_tacker
            'offer.delete',
            instance.id)
        ws_sender.send_message(
            f"user_{instance.runner_id}",  # tack_id_runner
            'runnertack.delete',
            instance.id)


@receiver(signal=post_save, sender=Offer)
def offer_cancelled(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"offer_cancelled. {instance.status = }")
    if not created and instance.status == OfferStatus.CANCELLED:
        ws_sender.send_message(
            f"user_{instance.tack.tacker_id}",  # tack_id_tacker
            'tack.delete',
            instance.tack_id)
        ws_sender.send_message(
            f"user_{instance.runner_id}",  # tack_id_runner
            'runnertack.delete',
            instance.id)


@receiver(signal=post_save, sender=Tack)
def tack_created_first_time(instance: Tack, created: bool, *args, **kwargs):
    logger.warning(f"tack_created_first_time. {instance.status = }")
    if created and instance.status == TackStatus.CREATED:
        # Workaround on a problem to fly-calculate data for every User of the Group
        # This message model is GroupTackSerializer with hard-coded is_mine_offer_sent field
        tack_serializer = TackDetailSerializer(instance)
        message = {
                    'id': instance.id,
                    'tack': tack_serializer.data,
                    'is_mine_offer_sent': False
                  }
        ws_sender.send_message(
            f"group_{instance.group_id}",
            'grouptack.create',
            message)
        ws_sender.send_message(
            f"user_{instance.tacker_id}",
            'tack.create',
            tack_serializer.data)


@receiver(signal=post_save, sender=Tack)
def tack_created_active_update(instance: Tack, created: bool, *args, **kwargs):
    logger.warning(f"tack_created_active_update. {instance.status = }")
    if not created and instance.status in (TackStatus.CREATED, TackStatus.ACTIVE):
        tack_serializer = TackDetailSerializer(instance)
        logging.getLogger().warning(f"if instance.status in (TackStatus.CREATED, TackStatus.ACTIVE):")
        message = {
            'id': instance.id,
            'tack': tack_serializer.data,
            'is_mine_offer_sent': False
        }
        runner_message = {
            'id': instance.id,
            'tack': tack_serializer.data,
            'is_mine_offer_sent': True
        }
        ws_sender.send_message(
            f"group_{instance.group_id}",
            'grouptack.update',
            message)
        ws_sender.send_message(
            f"user_{instance.tacker_id}",
            'tack.update',
            tack_serializer.data)
        ws_sender.send_message(
            f"tack_{instance.id}_offer",
            'grouptack.update',
            runner_message)
        ws_sender.send_message(
            f"user_{instance.runner_id}",
            'grouptack.update',
            runner_message)


@receiver(signal=post_save, sender=Tack)
def tack_status_accepted(instance: Tack, created: bool, *args, **kwargs):
    logger.warning(f"tack_status_accepted. {instance.status = }")
    if not created and instance.status == TackStatus.ACCEPTED:
        ws_sender.send_message(
            f"group_{instance.group_id}",
            'grouptack.delete',
            instance.id)  # group_id?
        ws_sender.send_message(
            f"user_{instance.tacker_id}",
            'tack.update',
            TackDetailSerializer(instance).data)
        ws_sender.send_message(
            f"user_{instance.runner_id}",
            'runnertack.update',
            TacksOffersSerializer(instance.accepted_offer).data)


@receiver(signal=post_save, sender=Tack)
def tack_status_accepted_in_progress_waiting_review(instance: Tack, created: bool, *args, **kwargs):
    logger.warning(f"tack_status_accepted_in_progress_waiting_review. {instance.status = }")
    if not created and \
            instance.status in (
                TackStatus.IN_PROGRESS,
                TackStatus.WAITING_REVIEW
    ):
        ws_sender.send_message(
            f"user_{instance.tacker_id}",
            'tack.update',
            TackDetailSerializer(instance).data)
        ws_sender.send_message(
            f"user_{instance.runner_id}",
            'runnertack.update',
            TacksOffersSerializer(instance.accepted_offer).data)


@receiver(signal=post_save, sender=Tack)
def tack_status_finished(instance: Tack, created: bool, *args, **kwargs):
    logger.warning(f"tack_status_finished. {instance.status = }")
    if not created and instance.status == TackStatus.FINISHED:
        ws_sender.send_message(
            f"user_{instance.tacker_id}",
            'tack.delete',
            instance.id)
        ws_sender.send_message(
            f"user_{instance.runner_id}",
            'runnertack.delete',
            instance.accepted_offer.id)
        ws_sender.send_message(
            f"user_{instance.runner_id}",
            'completedtackrunner.create',
            TackDetailSerializer(instance).data)


@receiver(signal=post_save, sender=Offer)
def send_offer_expired_notification(instance: Offer, *args, **kwargs):
    logger.warning(f"send_offer_expired_notification. {instance.status = }")
    if not instance.is_active:
        data = {
            "tack_price": instance.price,
            "tack_title": instance.tack.title
        }
        messages = create_message(data, ("offer_expired",))
        devices = FCMDevice.objects.filter(user=instance.runner)
        send_message(messages, (devices,))
    else:
        data = {
            "runner_firstname": instance.runner.first_name,
            "runner_lastname": instance.runner.last_name,
            "tack_title": instance.tack.title
        }
        messages = create_message(data, ("offer_received", ))
        devices = FCMDevice.objects.filter(user=instance.tack.tacker)
        send_message(messages, (devices,))


@receiver(signal=post_save, sender=Tack)
def finish_tack_notification(instance: Tack, *args, **kwargs):
    logger.warning(f"finish_tack_notification. {instance.status = }")
    data = {
        "runner_firstname": instance.runner.first_name,
        "runner_lastname": instance.runner.last_name,
        "tacker_firstname": instance.tacker.first_name,
        "tack_title": instance.title,
        "tack_price": instance.price,
    } if instance.status in (
            TackStatus.WAITING_REVIEW,
            TackStatus.IN_PROGRESS,
            TackStatus.FINISHED
    ) else dict()
    if instance.status == TackStatus.IN_PROGRESS:
        messages = create_message(data, ("in_progress",))
        devices_tacker = FCMDevice.objects.filter(user=instance.tacker)
        send_message(messages, (devices_tacker,))
        tack_expire_soon.apply_async(
            countdown=calculate_tack_expiring(instance.estimation_time_seconds),
            kwargs={
                "user_id": instance.runner_id,
                "nf_types": ("tack_expiring", ),
                "data": data,
            }
        )
    if instance.status == TackStatus.WAITING_REVIEW:
        ws_sender.send_message(
            f"user_{instance.tacker_id}",
            'tack.update',
            TackDetailSerializer(instance).data)
        ws_sender.send_message(
            f"user_{instance.runner_id}",
            'runnertack.update',
            TacksOffersSerializer(instance.accepted_offer).data)
        # data = {
        #     "runner_firstname": instance.runner.first_name,
        #     "tacker_firstname": instance.tacker.first_name,
        #     "tack_title": instance.title,
        # }
        messages = create_message(data, ("waiting_review", "pending_review"))
        runner_devices = FCMDevice.objects.filter(user=instance.runner)
        tacker_devices = FCMDevice.objects.filter(user=instance.tacker)
        send_message(messages, (tacker_devices, runner_devices))
    if instance.status == TackStatus.FINISHED:
        # data = {
        #     "tack_price": instance.price,
        #     "tack_title": instance.title,
        # }
        messages = create_message(data, ("finished", ))
        logger.warning(f"INSIDE SIGNAL {instance.runner = }")
        logger.warning(f"INSIDE SIGNAL {instance.runner_id = }")
        logger.warning(f"INSIDE SIGNAL {instance.runner.id = }")
        devices = FCMDevice.objects.filter(user=instance.runner)
        logger.warning(f"INSIDE SIGNAL {devices = }")
        send_message(messages, (devices,))


@receiver(signal=post_save, sender=Offer)
def offer_is_accepted_notification(instance: Offer, *args, **kwargs):
    logger.warning(f"offer_is_accepted_notification. {instance.status = }")
    if instance.status == OfferStatus.ACCEPTED:
        data = {
            "tack_price": instance.price,
            "tack_title": instance.tack.title,
            "runner_firstname": instance.runner.first_name
        }
        messages = create_message(data, ("offer_accepted", "in_preparing"))
        runner_devices = FCMDevice.objects.filter(user=instance.runner)
        tacker_devices = FCMDevice.objects.filter(user=instance.tack.tacker)
        send_message(messages, (runner_devices, tacker_devices))


@receiver(signal=post_save, sender=Tack)
def tack_is_created_notification(instance: Tack, created: bool, *args, **kwargs):
    logger.warning(f"tack_is_created_notification. {instance.status = }")
    if created:
        data = {
            "group_name": instance.group.name,
            "tack_description": instance.description,
            "tack_price": instance.price,
            "tack_title": instance.title
        }
        devices = FCMDevice.objects.filter(user__in=Subquery(
            GroupMembers.objects.filter(
                group=instance.group,
                is_muted=False
            ).exclude(
                member=instance.tacker
            ).values_list("member", flat=True)
        ))
        messages = create_message(data, ("tack_created",))
        send_message(messages, (devices, ))
        tack_long_inactive.apply_async(
            countdown=TACK_WITHOUT_OFFER_TIME,
            kwargs={
                "tack_id": instance.id,
                "user_id": instance.tacker.id,
                "data": data,
                "nf_types": ("no_offers_to_tack", )
            }
        )
