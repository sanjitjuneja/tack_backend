from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Subquery
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.choices import TackStatus
from group.models import GroupTacks, GroupMembers
from tack.models import Offer, Tack
from .tasks import delete_offer_task
from core.choices import TackStatus

from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification
# device = FCMDevice.objects.all().first()
message = Message(
    notification=Notification(title="title", body="First one", image="url"),
)
Message(
    data={
        "type": "Group",
        "img_url": "img",
        "group": "group_id",
        "tack_id": "tack_id",
        "Nick": "Mario",
        "body": "great match!",
        "Room": "PortugalVSDenmark"
   },
)


def build_body(data):
    body_mapping = {
        "tack_created": f"In group {data.get('group_name')} was added a new tack {data.get('tack_name')}",
        "offer_expired": f"Your offer {data.get('offer')} for tack {data.get('tack_name')} is expired",
        "offer_is_accepted": f" Your offer {data.get('offer')} for tack {data.get('tack_name')} is accepted",
        "waiting_review": f"Your tack {data.get('tack_name')} is completed and waiting review",
        "in_progress": f"Your tack {data.get('tack_name')} is in progress",
        "finished": f"Tack {data.get('tack_name')} has been reviewed and completed, money has been sent to your balance"
    }
    return body_mapping


def select_body(body: dict, type_message: str) -> str:
    return body.get(type_message)


"In group {group_name} was added a new tack {tack_name}"
messages = {
    "send_offer_expired_notification": "Your offer has expired"
}


def build_notification_message(title: str, body: str, image_url: str = None):
    return Message(
        notification=Notification(title=title, body=body, image=image_url),
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
def send_offer_expired_notification(instance: Offer, *args, **kwargs):
    if not instance.is_active:
        devices = FCMDevice.objects.filter(user=instance.runner)
        devices.send_message(message)


@receiver(signal=post_save, sender=Tack)
def finish_tack_notification(instance: Tack, *args, **kwargs):
    if instance.status in (TackStatus.WAITING_REVIEW, TackStatus.IN_PROGRESS):
        devices = FCMDevice.objects.filter(user=instance.tacker)
        devices.send_message(message)
    if instance.status == TackStatus.FINISHED:
        devices = FCMDevice.objects.filter(user=instance.runner)
        devices.send_message(message)


@receiver(signal=post_save, sender=Offer)
def offer_is_accepted_notification(instance: Offer, *args, **kwargs):
    if instance.is_accepted:
        devices = FCMDevice.objects.filter(user=instance.runner)
        devices.send_message(message)


@receiver(signal=post_save, sender=Tack)
def tack_is_created_notification(instance: Tack, created: bool, *args, **kwargs):
    if created:
        devices = FCMDevice.objects.filter(user__in=Subquery(
            GroupMembers.objects.filter(
                group=instance.group,
                is_muted=False
            ).values_list("member", flat=True)
        ))
        #data = {"group_name": instance.group}
        devices.send_message(message)
