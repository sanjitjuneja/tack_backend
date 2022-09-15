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

logger = logging.getLogger()


def build_title_body(data: dict) -> dict:
    nf_type_dict = {
        "tack_created": {
            "title": f"{data.get('group_name')} - {data.get('tack_description')}",
            "body": f"{data.get('tack_price')} - {data.get('tack_title')}"
        },
        "no_offers_to_tack": {
            "title": f"No Current Offers - {data.get('tack_title')}",
            "body": f"{data.get('group_name')} - Try increasing your Tack price to attract more Runners"
        },
        "offer_received": {
            "title": f"Offer Received - {data.get('runner_firstname')} {data.get('runner_lastname')}",
            "body": f"{data.get('tack_title')} - Accept Runner’s offer to start Tack"
        },
        "in_preparing": {
            "title": f"Tack Started - {data.get('runner_firstname')} Is Preparing",
            "body": (f"{data.get('tack_title')} - {data.get('runner_firstname')} "
                     f"{data.get('runner_lastname')} is preparing to begin completion")
        },
        "in_progress": {
            "title": f"Tack Completing - {data.get('runner_firstname')} Is Completing",
            "body": f"{data.get('tack_title')} - {data.get('runner_firstname')}"
        },
        "waiting_review": {
            "title": f"Review Completion - {data.get('runner_firstname')} Is Done",
            "body": f"{data.get('tack_title')} - Review completion of Tack before Runner receives funds",
        },
        "offer_expired": {
            "title": f"{data.get('tack_price')} Offer Expired - {data.get('tack_title')}",
            "body": "Your offer has expired, browse other Tacks on the home feed or place another offer",
        },
        "offer_accepted": {
            "title": f"{data.get('tack_price')} Offer Accepted - {data.get('tack_title')}",
            "body": "Offer accepted! Mark Tack as in progress to begin completion"
        },
        "tack_expiring": {
            "title": f"TACK EXPIRING - {data.get('tack_title')}",
            "body": ("Tack’s estimated completion time will expire soon. "
                     "Please complete Tack as soon as possible")
        },
        "pending_review": {
            "title": f"Pending Review - {data.get('tack_title')}",
            "body": (f"{data.get('tacker_firstname')} is reviewing Tack’s completion. "
                     f"Funds will be sent after review is completed")
        },
        "finished": {
            "title": f"{data.get('tack_price')} Was Sent To Your Balance",
            "body": (f"{data.get('tack_title')} - Tacker review complete! "
                     f"Your Tack balance has increased by {data.get('tack_price')}")
        },
        "canceled": {
            "title": f"Tack Canceled - You Have Been Fully Refunded",
            "body": (f"{data.get('tack_title')} - Runner canceled Tack. We have fully "
                     f"refunded the listed Tack price into your Tack Balance.")
        }
    }
    return nf_type_dict


def map_body_title(nf_type_dict: dict, nf_types: tuple):
    return [nf_type_dict.get(nf_type) for nf_type in nf_types]

# def map_body_title(nf_type_dict: dict, nf_type: str):
#     return nf_type_dict.get(nf_type)


def create_message(data: dict, nf_types: tuple, image_url: str = None) -> list[Message]:
    title_body_list = map_body_title(build_title_body(data), nf_types)
    logger.warning(f"{data = }")
    logger.warning(f"{nf_types = }")
    logger.warning(f"{image_url = }")
    logger.warning(f"{title_body_list = }")
    logger.warning(f"{type(title_body_list) = }")
    for obj in title_body_list:
        logger.warning(f"{obj = }")
    return [
            Message(
                notification=Notification(
                    title=message.get("title"),
                    body=message.get("body"),
                    image=image_url
                ),
                android=AndroidConfig(
                    ttl=datetime.timedelta(seconds=3600),
                    priority='high',
                    notification=AndroidNotification(
                        icon='stock_ticker_update',
                        color='#f45342',
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
            ) for message in title_body_list
    ]


# def create_notification_message(data: dict, nf_type: tuple, image_url: str = None):
#     title_body = map_body_title(build_title_body(data), nf_type)
#     return Message(
#         notification=Notification(
#             title=title_body.get("title"),
#             body=title_body.get("body"),
#             image=image_url
#         ),
#         # android=android,
#         # apns=apns
#     )


def send_message(messages: list, devices_list_of_queryset: tuple) -> None:
    logger.warning(f"Message inside send_message {messages = }")
    logger.warning(f" inside send_message {devices_list_of_queryset = }")
    for message, devices in zip(messages, devices_list_of_queryset):
        logger.warning(f"{message = }")
        logger.warning(f"{devices = }")
        devices.send_message(message,)
