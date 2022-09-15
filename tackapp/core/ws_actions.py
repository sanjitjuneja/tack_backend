import logging

from tack.models import Offer
from tack.serializers import TackDetailSerializer, OfferSerializer, TacksOffersSerializer
from tackapp.websocket_messages import WSSender

ws_sender = WSSender()
logger = logging.getLogger("core.ws_actions")


def ws_offer_created(instance: Offer):
    logger.warning(f"offer_created. {instance.status = }")
    logger.warning(f"if created:")
    tack_serializer = TackDetailSerializer(instance.tack)
    message_for_runner = {
        'id': instance.tack_id,
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
        f"tack_{instance.tack_id}_offer",
        "grouptack.update",
        message_for_runner
    )
    ws_sender.send_message(
        f"user_{instance.runner_id}",
        'grouptack.update',
        message_for_runner)


def ws_offer_accepted(instance: Offer):
    logger.warning(f"offer_accepted. {instance.status = }")
    ws_sender.send_message(
        f"user_{instance.tack.tacker_id}",  # tack_{instance.tack_id}_tacker
        'tack.update',
        TackDetailSerializer(instance.tack).data)
    ws_sender.send_message(
        f"user_{instance.tack.runner_id}",  # tack_{instance.tack_id}_runner
        'runnertack.update',
        TacksOffersSerializer(instance).data)


def ws_offer_in_progress(instance: Offer):
    logger.warning(f"offer_in_progress. {instance.status = }")
    ws_sender.send_message(
        f"user_{instance.tack.tacker_id}",  # tack_{instance.tack_id}_tacker
        'tack.update',
        TackDetailSerializer(instance.tack).data)
    ws_sender.send_message(
        f"user_{instance.tack.runner_id}",  # tack_{instance.tack_id}_runner
        'runnertack.update',
        TacksOffersSerializer(instance).data)


def ws_offer_finished(instance: Offer):
    logger.warning(f"offer_finished. {instance.status = }")
    ws_sender.send_message(
        f"user_{instance.tack.tacker_id}",  # tack_id_tacker
        'offer.delete',
        instance.id)
    ws_sender.send_message(
        f"user_{instance.runner_id}",  # tack_id_runner
        'runnertack.delete',
        instance.id)


def ws_offer_expired(instance: Offer):
    logger.warning(f"offer_expired. {instance.status = }")
    ws_sender.send_message(
        f"user_{instance.tack.tacker_id}",  # tack_id_tacker
        'offer.delete',
        instance.id)
    ws_sender.send_message(
        f"user_{instance.runner_id}",  # tack_id_runner
        'runnertack.delete',
        instance.id)


def ws_offer_deleted(instance: Offer):
    logger.warning(f"offer_deleted. {instance.status = }")
    tack_serializer = TackDetailSerializer(instance.tack)
    message_for_runner = {
        'id': instance.tack_id,
        'tack': tack_serializer.data,
        'is_mine_offer_sent': False
    }
    ws_sender.send_message(
        f"user_{instance.tack.tacker_id}",  # tack_id_tacker
        'offer.delete',
        instance.id)
    ws_sender.send_message(
        f"user_{instance.runner_id}",  # tack_id_runner
        'runnertack.delete',
        instance.id)
    ws_sender.send_message(
        f"user_{instance.runner_id}",  # tack_id_runner
        'grouptack.update',
        message_for_runner)


def ws_offer_cancelled(instance: Offer):
    logger.warning(f"offer_cancelled. {instance.status = }")
    ws_sender.send_message(
        f"user_{instance.tack.tacker_id}",  # tack_id_tacker
        'tack.delete',
        instance.tack_id)
    ws_sender.send_message(
        f"user_{instance.runner_id}",  # tack_id_runner
        'runnertack.delete',
        instance.id)
    ws_sender.send_message(
        f"user_{instance.tack.tacker_id}",  # tack_id_tacker
        "canceltackertackrunner.create",
        TackDetailSerializer(instance.tack).data)

