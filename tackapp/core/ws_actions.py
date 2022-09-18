import logging

from tack.models import Offer, Tack
from tack.serializers import TackDetailSerializer, OfferSerializer, TacksOffersSerializer
from tackapp.websocket_messages import WSSender

ws_sender = WSSender()
logger = logging.getLogger("core.ws_actions")


def ws_offer_created(offer: Offer):
    logger.warning(f"offer_created. {offer.status = }")
    logger.warning(f"if created:")
    tack_serializer = TackDetailSerializer(offer.tack)
    message_for_runner = {
        'id': offer.tack_id,
        'tack': tack_serializer.data,
        'is_mine_offer_sent': True
    }
    ws_sender.send_message(
        f"user_{offer.tack.tacker_id}",  # tack_{offer.tack_id}_tacker
        'offer.create',
        OfferSerializer(offer).data)
    ws_sender.send_message(
        f"user_{offer.runner_id}",
        'runnertack.create',
        TacksOffersSerializer(offer).data)
    ws_sender.send_message(
        f"tack_{offer.tack_id}_offer",
        "grouptack.update",
        message_for_runner
    )
    ws_sender.send_message(
        f"user_{offer.runner_id}",
        'grouptack.update',
        message_for_runner)


def ws_offer_accepted(offer: Offer):
    logger.warning(f"offer_accepted. {offer.status = }")
    ws_sender.send_message(
        f"user_{offer.tack.tacker_id}",  # tack_{offer.tack_id}_tacker
        'tack.update',
        TackDetailSerializer(offer.tack).data)
    ws_sender.send_message(
        f"user_{offer.tack.runner_id}",  # tack_{offer.tack_id}_runner
        'runnertack.update',
        TacksOffersSerializer(offer).data)


def ws_offer_in_progress(offer: Offer):
    logger.warning(f"offer_in_progress. {offer.status = }")
    ws_sender.send_message(
        f"user_{offer.tack.tacker_id}",  # tack_{offer.tack_id}_tacker
        'tack.update',
        TackDetailSerializer(offer.tack).data)
    ws_sender.send_message(
        f"user_{offer.tack.runner_id}",  # tack_{offer.tack_id}_runner
        'runnertack.update',
        TacksOffersSerializer(offer).data)


def ws_offer_finished(offer: Offer):
    logger.warning(f"offer_finished. {offer.status = }")
    ws_sender.send_message(
        f"user_{offer.tack.tacker_id}",  # tack_id_tacker
        'offer.delete',
        offer.id)
    ws_sender.send_message(
        f"user_{offer.runner_id}",  # tack_id_runner
        'runnertack.delete',
        offer.id)


def ws_offer_expired(offer: Offer):
    logger.warning(f"offer_expired. {offer.status = }")
    ws_sender.send_message(
        f"user_{offer.tack.tacker_id}",  # tack_id_tacker
        'offer.delete',
        offer.id)
    ws_sender.send_message(
        f"user_{offer.runner_id}",  # tack_id_runner
        'runnertack.delete',
        offer.id)


def ws_offer_deleted(offer: Offer):
    logger.warning(f"offer_deleted. {offer.status = }")
    tack_serializer = TackDetailSerializer(offer.tack)
    message_for_runner = {
        'id': offer.tack_id,
        'tack': tack_serializer.data,
        'is_mine_offer_sent': False
    }
    ws_sender.send_message(
        f"user_{offer.tack.tacker_id}",  # tack_id_tacker
        'offer.delete',
        offer.id)
    ws_sender.send_message(
        f"user_{offer.runner_id}",  # tack_id_runner
        'runnertack.delete',
        offer.id)
    ws_sender.send_message(
        f"user_{offer.runner_id}",  # tack_id_runner
        'grouptack.update',
        message_for_runner)


def ws_offer_cancelled(offer: Offer):
    logger.warning(f"offer_cancelled. {offer.status = }")
    ws_sender.send_message(
        f"user_{offer.tack.tacker_id}",  # tack_id_tacker
        'tack.delete',
        offer.tack_id)
    ws_sender.send_message(
        f"user_{offer.runner_id}",  # tack_id_runner
        'runnertack.delete',
        offer.id)
    ws_sender.send_message(
        f"user_{offer.tack.tacker_id}",  # tack_id_tacker
        "canceltackertackrunner.create",
        TackDetailSerializer(offer.tack).data)


def ws_tack_created(tack: Tack):
    logger.warning(f"tack_created_first_time. {tack.status = }")

    tack_serializer = TackDetailSerializer(tack)
    # Workaround on a problem to fly-calculate data for every User of the Group
    # This message model is GroupTackSerializer with hard-coded is_mine_offer_sent field
    # Because on creating new Tack can not be any Offers to this Tack
    message = {
        'id': tack.id,
        'tack': tack_serializer.data,
        'is_mine_offer_sent': False
    }
    ws_sender.send_message(
        f"group_{tack.group_id}",
        'grouptack.create',
        message)
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        'tack.create',
        tack_serializer.data)


def ws_tack_deleted(tack: Tack):
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        "tack.delete",
        tack.id
    )
    ws_sender.send_message(
        f"group_{tack.group_id}",
        "grouptack.delete",
        tack.id
    )


def ws_tack_cancelled(tack: Tack):
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        "tack.delete",
        tack.id
    )
    ws_sender.send_message(
        f"user_{tack.runner_id}",
        "runnertack.delete",
        tack.accepted_offer_id
    )


def ws_tack_created_from_active(tack: Tack):
    logger.warning(f"tack_created_active_update. {tack.status = }")
    tack_serializer = TackDetailSerializer(tack)
    logging.getLogger().warning(f"if tack.status in (TackStatus.CREATED, TackStatus.ACTIVE):")
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        'tack.update',
        tack_serializer.data)
    ws_sender.send_message(
        f"group_{tack.group_id}",
        'grouptack.update',
        tack_serializer.data)


def ws_tack_active(tack: Tack):
    logger.warning(f"tack_created_active_update. {tack.status = }")
    tack_serializer = TackDetailSerializer(tack)
    logging.getLogger().warning(f"if tack.status in (TackStatus.CREATED, TackStatus.ACTIVE):")
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        'tack.update',
        tack_serializer.data)


def ws_tack_accepted(tack: Tack):
    logger.warning(f"tack_status_accepted. {tack.status = }")
    ws_sender.send_message(
        f"group_{tack.group_id}",
        'grouptack.delete',
        tack.id)
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        'tack.update',
        TackDetailSerializer(tack).data)
    ws_sender.send_message(
        f"user_{tack.runner_id}",
        'runnertack.update',
        TacksOffersSerializer(tack.accepted_offer).data)


def ws_tack_in_progress(tack: Tack):
    logger.warning(f"tack_status_accepted_in_progress_waiting_review. {tack.status = }")
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        'tack.update',
        TackDetailSerializer(tack).data)
    ws_sender.send_message(
        f"user_{tack.runner_id}",
        'runnertack.update',
        TacksOffersSerializer(tack.accepted_offer).data)


def ws_tack_waiting_review(tack: Tack):
    logger.warning(f"tack_status_accepted_in_progress_waiting_review. {tack.status = }")
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        'tack.update',
        TackDetailSerializer(tack).data)
    ws_sender.send_message(
        f"user_{tack.runner_id}",
        'runnertack.update',
        TacksOffersSerializer(tack.accepted_offer).data)


def ws_tack_finished(tack: Tack):
    logger.warning(f"tack_status_finished. {tack.status = }")
    ws_sender.send_message(
        f"user_{tack.tacker_id}",
        'tack.delete',
        tack.id)
    ws_sender.send_message(
        f"user_{tack.runner_id}",
        'runnertack.delete',
        tack.accepted_offer.id)
    ws_sender.send_message(
        f"user_{tack.runner_id}",
        'completedtackrunner.create',
        TackDetailSerializer(tack).data)
