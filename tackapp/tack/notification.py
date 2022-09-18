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

from payment.services import convert_to_decimal
from tack.models import Tack, Offer

logger = logging.getLogger("tack.notification")


def build_title_body_from_offer(message_type: str, offer: Offer) -> tuple:
    ntf_type_dict = {
        "offer_received": {
            "title": "Offer Received - {runner_first_name} {runner_last_name}",
            "body": "{tack_title} - Accept Runner’s offer to start Tack"
        },
        "offer_accepted": {
            "title": "${tack_or_offer_price} Offer Accepted - {tack_title}",
            "body": "Offer accepted! Mark Tack as in progress to begin completion"
        },
        "tack_expiring": {
            "title": "TACK EXPIRING - {tack_title}",
            "body": ("Tack’s estimated completion time will expire soon. "
                     "Please complete Tack as soon as possible")
        },
        "offer_expired": {
            "title": "${tack_or_offer_price} Offer Expired - {tack_title}",
            "body": "Your offer has expired, browse other Tacks on the home feed or place another offer",
        },
    }
    pickled_message = ntf_type_dict.get(message_type)
    return (
        pickled_message.get("title"),
        pickled_message.get("body"),
        pickled_message.get("image_url")
    )


def build_title_body_from_tack(message_type: str, tack: Tack) -> tuple:
    ntf_type_dict = {
        "tack_created": {
            "title": "{group_name} - {tack_description}",
            "body": "${tack_price} - {tack_title}"
        },
        "no_offers_to_tack": {
            "title": "No Current Offers - {tack_title}",
            "body": "{group_name} - Try increasing your Tack price to attract more Runners"
        },
        "in_preparing": {
            "title": "Tack Started - {runner_first_name} Is Preparing",
            "body": ("{tack_title} - {runner_first_name} {runner_last_name} "
                     "is preparing to begin completion")
        },
        "in_progress": {
            "title": "Tack Completing - {runner_first_name} Is Completing",
            "body": "{tack_title} - {runner_first_name}"
        },
        "waiting_review": {
            "title": "Review Completion - {runner_first_name} Is Done",
            "body": "{tack_title} - Review completion of Tack before Runner receives funds",
        },
        "finished": {
            "title": "${tack_price} Was Sent To Your Balance",
            "body": ("{tack_title} - Tacker review complete! "
                     "Your Tack balance has increased by ${tack_price}")
        },
        "canceled": {
            "title": "Tack Canceled - You Have Been Fully Refunded",
            "body": ("{tack_title} - Runner canceled Tack. We have fully "
                     "refunded the listed Tack price into your Tack Balance.")
        }
    }
    pickled_message = ntf_type_dict.get(message_type)
    return (
        pickled_message.get("title"),
        pickled_message.get("body"),
        pickled_message.get("image_url")
    )


def get_formatted_ntf_title_body_from_tack(ntf_title: str, ntf_body: str, tack: Tack):
    tacker = tack.tacker
    runner = tack.runner
    group = tack.group

    tack_dict = {
        "tack_title": tack.title,
        "tack_type": tack.type,
        "tack_price": str(convert_to_decimal(tack.price)),
        "tack_description": tack.description,
        "tack_status": tack.status,
        "tack_completion_message": tack.completion_message,
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
    formatted_ntf_title = ntf_title.format(
        **tack_dict,
        **tacker_dict,
        **runner_dict,
        **group_dict,
    )
    formatted_ntf_body = ntf_body.format(
        **tack_dict,
        **tacker_dict,
        **runner_dict,
        **group_dict,
    )
    return formatted_ntf_title, formatted_ntf_body


def get_formatted_ntf_title_body_from_offer(ntf_title: str, ntf_body: str, offer: Offer):
    tack = offer.tack
    tacker = tack.tacker
    runner = offer.runner
    group = tack.group
    tack_or_offer_price = str(convert_to_decimal(offer.price or tack.price))


    tack_dict = {
        "tack_title": tack.title,
        "tack_type": tack.type,
        "tack_price": str(convert_to_decimal(tack.price)),
        "tack_description": tack.description,
        "tack_status": tack.status,
        "tack_completion_message": tack.completion_message,
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
    formatted_ntf_title = ntf_title.format(
        **tack_dict,
        **tacker_dict,
        **runner_dict,
        **group_dict,
        tack_or_offer_price=tack_or_offer_price
    )
    formatted_ntf_body = ntf_body.format(
        **tack_dict,
        **tacker_dict,
        **runner_dict,
        **group_dict,
        tack_or_offer_price=tack_or_offer_price
    )
    return formatted_ntf_title, formatted_ntf_body


def build_ntf_message(title: str = None, body: str = None, image_url: str = None):
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
