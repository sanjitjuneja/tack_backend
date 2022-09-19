import logging
import datetime

from firebase_admin.messaging import (
    Message,
    Notification,
    Aps,
    AndroidConfig,
    APNSConfig,
    AndroidNotification,
    APNSPayload
)

from core.choices import NotificationType
from payment.services import convert_to_decimal
from tack.models import Tack, Offer

logger = logging.getLogger("tack.notification")
ntf_type_dict = {
        NotificationType.TACK_CREATED: {
            "title": "Tack",
            "body": "{group_name}: {tack_price} - {tack_title}"
        },
        NotificationType.TACK_INACTIVE: {
            "title": "Tack",
            "body": "No Current Offers - {tack_title"
        },
        NotificationType.OFFER_RECEIVED: {
            "title": "ACCEPT OFFER",
            "body": "{tack_title} - Received Offer From {runner_first_name} {runner_last_name}"
        },
        NotificationType.COUNTEROFFER_RECEIVED: {
            "title": "ACCEPT OFFER",
            "body": ("{tack_title} - Received {tack_or_offer_price} Counter Offer From "
                     "{runner_first_name} {runner_last_name}. Accept now to begin Tack")
        },
        NotificationType.TACK_ACCEPTED: {
            "title": "Tack",
            "body": "{runner_first_name} {runner_last_name} Is Preparing - {tack_title}"
        },
        NotificationType.TACK_IN_PROGRESS: {
            "title": "Tack",
            "body": "{runner_first_name} {runner_last_name} Is Completing - {tack_title}"
        },
        NotificationType.RUNNER_FINISHED: {
            "title": "REVIEW COMPLETION",
            "body": ("{runner_first_name} {runner_last_name} Is Done: "
                     "Review Tack’s completion before funds are sent - {tack_title}")
        },
        NotificationType.TACK_CANCELLED: {
            "title": "Tack",
            "body": "Runner Canceled Tack: You Have Been Fully Refunded - {tack_title}"
        },
        NotificationType.OFFER_ACCEPTED: {
            "title": "BEGIN TACK",
            "body": "{tack_title} - Your {tack_or_offer_price} offer was accepted. Begin Tack to start completion"
        },
        NotificationType.OFFER_EXPIRED: {
            "title": "Tack",
            "body": "{tack_or_offer_price} Offer Expired - {tack_title}",
        },
        NotificationType.TACK_EXPIRING: {
            "title": "TACK EXPIRING",
            "body": ("{tack_title} - Tack’s estimated completion time will expire soon. "
                     "Please complete Tack as soon as possible")
        },
        NotificationType.TACK_WAITING_REVIEW: {
            "title": "Tack",
            "body": ("{tacker_first_name} {tacker_last_name} is reviewing Tack’s completion. "
                     "Funds will be sent after review is completed - {tack_title}")
        },
        NotificationType.TACK_FINISHED: {
            "title": "Tack",
            "body": ("{tack_title} - Tacker review complete! "
                     "Tack Complete: {tack_price} Was Sent To Your Balance - {tack_title}")
        },
    }


def get_message_template(message_type: NotificationType) -> tuple:
    selected_template = ntf_type_dict.get(message_type)
    return (
        selected_template.get("title"),
        selected_template.get("body"),
        selected_template.get("image_url")
    )


def get_properties_dict(instance: Tack | Offer):
    match type(instance):
        case Tack() as tack:
            tack = tack
            tacker = tack.tacker
            runner = tack.runner
            group = tack.group
            tack_or_offer_price = tack.price
        case Offer() as offer:
            tack = offer.tack
            tacker = tack.tacker
            runner = offer.runner
            group = tack.group
            tack_or_offer_price = str(convert_to_decimal(offer.price or offer.tack.price))
        case _:
            return dict()

    tack_dict = {
        "tack_title": tack.title,
        "tack_type": tack.type,
        "tack_price": str(convert_to_decimal(tack.price)),
        "tack_description": tack.description,
        "tack_status": tack.status,
        "tack_completion_message": tack.completion_message,
        "tack_or_offer_price": tack_or_offer_price
    } if tack else dict()
    tacker_dict = {
        "tacker_first_name": tacker.first_name,
        "tacker_last_name": tacker.last_name,
        "tacker_image": tacker.profile_picture,
        "tacker_phone_number": tacker.phone_number,
        "tacker_email": tacker.email,
        "tacker_birthday": tacker.birthday,
        "tacker_rating": tacker.tacks_rating,
        "tacker_tacks_completed": tacker.tacks_amount,
        "tacker_last_login": tacker.last_login,
    } if tacker else dict()
    runner_dict = {
        "runner_first_name": runner.first_name,
        "runner_last_name": runner.last_name,
        "runner_image": runner.profile_picture,
        "runner_phone_number": runner.phone_number,
        "runner_email": runner.email,
        "runner_birthday": runner.birthday,
        "runner_rating": runner.tacks_rating,
        "runner_tacks_completed": runner.tacks_amount,
        "runner_last_login": runner.last_login,
    } if runner else dict()
    group_dict = {
        "group_name": group.name,
        "group_description": group.description,
        "group_image": group.image,
        "group_invitation_link": group.invitation_link,
    } if group else dict()
    return {
        "tack": tack_dict,
        "tacker": tacker_dict,
        "runner": runner_dict,
        "group": group_dict
    }


def get_formatted_ntf_title_and_body(ntf_title: str, ntf_body: str, instance: Tack | Offer):
    properties = get_properties_dict(instance)
    # TODO: map function?
    formatted_ntf_title = ntf_title.format(
        **properties.get("tack"),
        **properties.get("tacker"),
        **properties.get("runner"),
        **properties.get("group"),
    )
    formatted_ntf_body = ntf_body.format(
        **properties.get("tack"),
        **properties.get("tacker"),
        **properties.get("runner"),
        **properties.get("group"),
    )
    return formatted_ntf_title, formatted_ntf_body


def _build_ntf_message(title: str = None, body: str = None, image_url: str = None):
    return Message(
        notification=Notification(
            title=title,
            body=body,
            image=image_url
        ),
        android=AndroidConfig(
            ttl=datetime.timedelta(seconds=3600),
            priority='high',
            notification=AndroidNotification(
                icon='stock_ticker_update',
                sound="default"
            ),
        ),
        apns=APNSConfig(
            payload=APNSPayload(
                aps=Aps(
                    sound="default",
                    content_available=1
                ),
            ),
        )
    )


def build_ntf_message(ntf_type: NotificationType, instance: Tack | Offer):
    logger.info(f"INSIDE build_ntf_message")
    ntf_title, ntf_body, ntf_image_url = get_message_template(ntf_type)
    formatted_ntf_title, formatted_ntf_body = get_formatted_ntf_title_and_body(ntf_title, ntf_body, instance)
    message = _build_ntf_message(formatted_ntf_title, formatted_ntf_body, ntf_image_url)
    return message
