from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from tackapp.settings import AWS_S3_CUSTOM_DOMAIN


class WSSender:
    channel_layer = get_channel_layer()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(WSSender, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.ws_group: str
        self.ws_type: str
        self.ws_message: dict

    @classmethod
    def send_message(cls, ws_group: str, ws_type: str, ws_message: dict | int):
        # ws_message = build_message_dict(ws_message)

        async_to_sync(cls.channel_layer.group_send)(
            ws_group,
            {
                'type': ws_type,
                'message': ws_message
            })


# def build_message_dict(dictionary: dict):
#     for key, value in dictionary.items():
#         if key == "image":
#             # dictionary[key] = build_image_url(value)
#             continue
#         elif isinstance(value, dict):
#             build_message_dict(value)
#
#     return dictionary
#
#
# def build_image_url(image_url: str) -> str:
#     return f"{AWS_S3_CUSTOM_DOMAIN}/{image_url}"
