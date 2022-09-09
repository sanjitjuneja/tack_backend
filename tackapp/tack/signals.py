from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.choices import TackStatus
from group.models import GroupTacks
from tack.models import Offer, Tack
from .tasks import delete_offer_task
from core.choices import TackStatus

from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification
# device = FCMDevice.objects.all().first()
message = Message(
    notification=Notification(title="title", body="First one", image="url"),
)
# device.send_message(Message)


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
def send_offer_expired(instance: Offer, *args, **kwargs):
    if not instance.is_active:
        devices = FCMDevice.objects.filter(user=instance.runner)
        devices.send_message(message)


@receiver(signal=post_save, sender=Tack)
def finish_tack_nofitication(instance: Tack, *args, **kwargs):
    if instance.status == TackStatus.FINISHED:
        devices = FCMDevice.objects.filter(user=instance.runner)
        devices.send_message(message)


@receiver(signal=post_save, sender=Offer)
def offer_is_accepted(instance: Offer, *args, **kwargs):
    if instance.is_accepted:
        devices = FCMDevice.objects.filter(user=instance.runner)
        devices.send_message(message)
