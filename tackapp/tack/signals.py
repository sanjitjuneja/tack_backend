import logging

from django.db.models import Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.choices import OfferStatus
from core.ws_actions import ws_offer_created, ws_offer_in_progress, ws_offer_finished, ws_offer_expired, \
    ws_offer_deleted, ws_offer_cancelled, ws_offer_accepted, ws_tack_created, ws_tack_deleted, ws_tack_cancelled, \
    ws_tack_created_from_active, ws_tack_active, ws_tack_accepted, ws_tack_in_progress, ws_tack_waiting_review, \
    ws_tack_finished
from group.models import GroupMembers
from tack.models import Offer, Tack
from tack.serializers import TackDetailSerializer, OfferSerializer, TacksOffersSerializer
from tackapp.websocket_messages import WSSender
from tack.tasks import set_expire_offer_task, tack_long_inactive, tack_expire_soon
from tack.services import calculate_tack_expiring
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
        task = set_expire_offer_task.apply_async(
            countdown=instance.lifetime_seconds,
            kwargs={"offer_id": instance.id}
        )
        logging.getLogger().info(f"run_delete_offer_task {task}")


@receiver(signal=post_save, sender=Offer)
def tack_status_on_offer_save(instance: Offer, *args, **kwargs):
    logger.warning(f"tack_status_on_offer_save. {instance.status = }")

    # if instance.status != OfferStatus.CREATED:
    #     return
    if instance.tack.status not in (TackStatus.CREATED, TackStatus.ACTIVE):
        return
    if instance.status in (OfferStatus.CREATED, OfferStatus.EXPIRED, OfferStatus.DELETED):
        related_offers = Offer.objects.filter(
            tack=instance.tack,
            status=OfferStatus.CREATED)
        match related_offers.count():
            case 0:
                instance.tack.change_status(TackStatus.CREATED)
            case 1:
                instance.tack.change_status(TackStatus.ACTIVE)


@receiver(signal=post_save, sender=Offer)
def offer_ws_actions(instance: Offer, created: bool, *args, **kwargs):
    match instance.status:
        case OfferStatus.CREATED:
            ws_offer_created(instance)
        case OfferStatus.ACCEPTED:
            ws_offer_accepted(instance)
        case OfferStatus.IN_PROGRESS:
            ws_offer_in_progress(instance)
        case OfferStatus.FINISHED:
            ws_offer_finished(instance)
        case OfferStatus.EXPIRED:
            ws_offer_expired(instance)
        case OfferStatus.DELETED:
            ws_offer_deleted(instance)
        case OfferStatus.CANCELLED:
            ws_offer_cancelled(instance)


@receiver(signal=post_save, sender=Tack)
def tack_ws_actions(instance: Tack, created: bool, *args, **kwargs):
    # initial creation from tacker
    if created:
        ws_tack_created(instance)
        return
    # tack deletion process
    if not instance.is_active:
        # deletion from tacker (tack should be in status CREATED)
        if instance.status == TackStatus.CREATED:
            ws_tack_deleted(instance)
            return
        # deletion(cancellation) from runner (tack might be in status ACCEPTED, IN_PROGRESS)
        if instance.is_canceled:
            ws_tack_cancelled(instance)
            return
    match instance.status:
        # status changed from active to created (all offers have been deleted)
        case TackStatus.CREATED:
            ws_tack_created_from_active(instance)
        # status changed from created to active (first offer was sent to this tack)
        case TackStatus.ACTIVE:
            ws_tack_active(instance)
        # status changed to accepted (tacker accepted offer)
        case TackStatus.ACCEPTED:
            ws_tack_accepted(instance)
        # status changed to in_progress (runner began tack completion)
        case TackStatus.IN_PROGRESS:
            ws_tack_in_progress(instance)
        # status changed to waiting_review (runner completed the tack)
        case TackStatus.WAITING_REVIEW:
            ws_tack_waiting_review(instance)
        # status changed to finished (tacker confirmed tack completion)
        case TackStatus.FINISHED:
            ws_tack_finished(instance)


@receiver(signal=post_save, sender=Offer)
def send_offer_expired_notification(instance: Offer, created: bool, *args, **kwargs):
    logger.warning(f"send_offer_expired_notification. {instance.status = }")
    if created:
        data = {
            "runner_firstname": instance.runner.first_name,
            "runner_lastname": instance.runner.last_name,
            "tack_title": instance.tack.title
        }
        messages = create_message(data, ("offer_received",))
        devices = FCMDevice.objects.filter(user=instance.tack.tacker)
        send_message(messages, (devices,))
    elif instance.status == OfferStatus.EXPIRED:
        data = {
            "tack_price": instance.price or instance.tack.price,
            "tack_title": instance.tack.title
        }
        messages = create_message(data, ("offer_expired",))
        devices = FCMDevice.objects.filter(user=instance.runner)
        send_message(messages, (devices,))


@receiver(signal=post_save, sender=Tack)
def send_tack_finished_notification(instance: Tack, *args, **kwargs):
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
        TackStatus.FINISHED,
    ) or instance.is_canceled else dict()
    if instance.status == TackStatus.IN_PROGRESS and instance.estimation_time_seconds:
        messages = create_message(data, ("in_progress",))
        devices_tacker = FCMDevice.objects.filter(user=instance.tacker)
        send_message(messages, (devices_tacker,))
        tack_expire_soon.apply_async(
            countdown=calculate_tack_expiring(instance.estimation_time_seconds),
            kwargs={
                "user_id": instance.runner_id,
                "nf_types": ("tack_expiring",),
                "data": data,
            }
        )
    if instance.is_canceled:
        messages = create_message(data, ("canceled",))
        devices_tacker = FCMDevice.objects.filter(user=instance.tacker)
        send_message(messages, (devices_tacker,))
    if instance.status == TackStatus.WAITING_REVIEW:
        ws_sender.send_message(
            f"user_{instance.tacker_id}",
            'tack.update',
            TackDetailSerializer(instance).data)
        ws_sender.send_message(
            f"user_{instance.runner_id}",
            'runnertack.update',
            TacksOffersSerializer(instance.accepted_offer).data)
        messages = create_message(data, ("waiting_review", "pending_review"))
        runner_devices = FCMDevice.objects.filter(user=instance.runner)
        tacker_devices = FCMDevice.objects.filter(user=instance.tacker)
        send_message(messages, (tacker_devices, runner_devices))
    if instance.status == TackStatus.FINISHED:
        messages = create_message(data, ("finished", ))
        devices = FCMDevice.objects.filter(user=instance.runner)
        logger.warning(f"INSIDE SIGNAL {devices = }")
        send_message(messages, (devices,))


@receiver(signal=post_save, sender=Offer)
def send_offer_accepted_notification(instance: Offer, *args, **kwargs):
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
def send_tack_created_notification(instance: Tack, created: bool, *args, **kwargs):
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
        logger.warning(f"INSIDE SIGNAL {devices = }")
        messages = create_message(data, ("tack_created",))

        send_message(messages, (devices, ))

        tack_without_offer_seconds = 900
        tack_long_inactive.apply_async(
            countdown=tack_without_offer_seconds,
            kwargs={
                "tack_id": instance.id,
                "user_id": instance.tacker.id,
                "data": data,
                "nf_types": ("no_offers_to_tack",)
            }
        )
