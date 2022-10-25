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
from tack.tasks import set_expire_offer_task, tack_long_inactive, tack_will_expire_soon, change_tack_status_finished
from tack.services import notification_on_tack_finished, notification_on_tack_waiting_review, \
    notification_on_tack_in_progress, notification_on_tack_cancelled, deferred_notification_tack_inactive, \
    notification_on_tack_created, notification_on_offer_expired, deferred_notification_tack_will_expire_soon, \
    notification_on_offer_accepted, notification_on_offer_created, notification_on_tack_accepted, \
    notification_on_offer_finished

from core.choices import TackStatus


ws_sender = WSSender()
logger = logging.getLogger('django')


@receiver(signal=post_save, sender=Offer)
def run_delete_offer_task(instance: Offer, created: bool, *args, **kwargs):
    logger.debug(f"run_delete_offer_task. {instance.status = }")
    if created:
        task = set_expire_offer_task.apply_async(
            countdown=instance.lifetime_seconds,
            kwargs={"offer_id": instance.id}
        )
        logger.debug(f"run_delete_offer_task {task}")


@receiver(signal=post_save, sender=Offer)
def tack_status_on_offer_save(instance: Offer, *args, **kwargs):
    logger.debug(f"tack_status_on_offer_save. {instance.status = }")

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
    logger.debug(f"### INSIDE offer_ws_actions signal ###")
    logger.debug(f"### OFFER {instance = }")
    logger.debug(f"### OFFER {instance.status = }")
    logger.debug(f"### OFFER.TACK {instance.tack.status = }")
    match instance.status:
        case OfferStatus.CREATED:
            if instance.tack.auto_accept:
                return
            ws_offer_created(instance)
            notification_on_offer_created(instance)
        case OfferStatus.ACCEPTED:
            ws_offer_accepted(instance)
            notification_on_offer_accepted(instance)
        case OfferStatus.IN_PROGRESS:
            ws_offer_in_progress(instance)
            deferred_notification_tack_will_expire_soon(instance)
        case OfferStatus.FINISHED:
            ws_offer_finished(instance)
            notification_on_offer_finished(instance)
        case OfferStatus.EXPIRED:
            ws_offer_expired(instance)
            notification_on_offer_expired(instance)
        case OfferStatus.DELETED:
            ws_offer_deleted(instance)
        case OfferStatus.CANCELLED:
            ws_offer_cancelled(instance)


@receiver(signal=post_save, sender=Tack)
def tack_ws_actions(instance: Tack, created: bool, *args, **kwargs):
    logger.debug(f"### INSIDE tack_ws_actions signal ###")
    logger.debug(f"### TACK {instance = }")
    logger.debug(f"### TACK {instance.status = }")
    # initial creation from tacker
    if created:
        ws_tack_created(instance)
        notification_on_tack_created(instance)
        deferred_notification_tack_inactive(instance)  # celery task on sending a notification after some amount of time
        return
    # tack deletion process
    if not instance.is_active:
        # deletion from tacker (tack should be in status CREATED or ACTIVE)
        if instance.status in (TackStatus.CREATED, TackStatus.ACTIVE):
            ws_tack_deleted(instance)
            return
        # deletion(cancellation) from runner (tack might be in status ACCEPTED, IN_PROGRESS)
        if instance.is_canceled:
            ws_tack_cancelled(instance)
            notification_on_tack_cancelled(instance)
            return
    match instance.status:
        # status changed from active to created (all offers have been deleted)
        case TackStatus.CREATED:
            ws_tack_created_from_active(instance)
        # status changed from created to active (first offer was sent to this tack)
        case TackStatus.ACTIVE:
            if instance.auto_accept:
                return
            ws_tack_active(instance)
        # status changed to accepted (tacker accepted offer)
        case TackStatus.ACCEPTED:
            ws_tack_accepted(instance)
            notification_on_tack_accepted(instance)
        # status changed to in_progress (runner began tack completion)
        case TackStatus.IN_PROGRESS:
            ws_tack_in_progress(instance)
            notification_on_tack_in_progress(instance)
        # status changed to waiting_review (runner completed the tack)
        case TackStatus.WAITING_REVIEW:
            ws_tack_waiting_review(instance)
            notification_on_tack_waiting_review(instance)
            change_tack_status_finished.apply_async(countdown=43200, kwargs={"tack_id": instance.id})
        # status changed to finished (tacker confirmed tack completion)
        case TackStatus.FINISHED:
            ws_tack_finished(instance)
            notification_on_tack_finished(instance)

