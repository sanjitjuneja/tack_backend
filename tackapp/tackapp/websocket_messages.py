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
        async_to_sync(cls.channel_layer.group_send)(
            ws_group,
            {
                'type': ws_type,
                'message': ws_message
            })
