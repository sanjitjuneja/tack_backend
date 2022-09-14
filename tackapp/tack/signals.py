from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Subquery
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from group.models import GroupTacks, GroupMembers
from tack.models import Offer, Tack
from .tasks import delete_offer_task, raise_price, tack_expire_soon
from .services import TACK_WITHOUT_OFFER_TIME, calculate_tack_expiring
from .notification import (
    create_message,
    send_message
)
from core.choices import TackStatus

from fcm_django.models import FCMDevice


@receiver(signal=post_save, sender=Offer)
def run_delete_offer_task(instance: Offer, created: bool, *args, **kwargs):
    if created:
        task = delete_offer_task.apply_async(
            countdown=instance.lifetime_seconds,
            kwargs={"offer_id": instance.id}
        )


@receiver(signal=post_save, sender=Offer)
def tack_status_on_offer_save(instance: Offer, *args, **kwargs):
    if Offer.objects.filter(tack=instance.tack).count() == 1:
        instance.tack.change_status(TackStatus.ACTIVE)


@receiver(signal=post_delete, sender=Offer)
def tack_status_on_offer_delete(instance: Offer, *args, **kwargs):
    if Offer.objects.filter(tack=instance.tack).count() == 0:
        instance.tack.change_status(TackStatus.CREATED)


@receiver(signal=post_save, sender=Offer)
def send_offer_expired_notification(instance: Offer, *args, **kwargs):
    if not instance.is_active:
        data = {
            "tack_price": instance.price,
            "tack_title": instance.tack.title
        }
        messages = create_message(data, ("offer_expired",))
        devices = FCMDevice.objects.filter(user=instance.runner)
        send_message(messages, devices)
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
        devices = FCMDevice.objects.filter(user=instance.runner)
        send_message(messages, (devices,))


@receiver(signal=post_save, sender=Offer)
def offer_is_accepted_notification(instance: Offer, *args, **kwargs):
    if instance.is_accepted:
        data = {
            "tack_price": instance.price,
            "tack_title": instance.tack.title,
            "runner_firstname": instance.runner.first_name
        }
        messages = create_message(data, ("offer_accepted", "in_preparing"))
        runner_devices = FCMDevice.objects.filter(user=instance.runner)
        tacker_devices = FCMDevice.objects.filter(user=instance.tack.tacker)
        send_message(messages, [runner_devices, tacker_devices])


@receiver(signal=post_save, sender=Tack)
def tack_is_created_notification(instance: Tack, created: bool, *args, **kwargs):
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
        send_message(messages, [devices, ])
        raise_price.apply_async(
            countdown=TACK_WITHOUT_OFFER_TIME,
            kwargs={
                "tack_id": instance.id,
                "user_id": instance.tacker.id,
                "data": data,
                "nf_types": ("no_offers_to_tack", )
            }
        )
