import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q

from core.choices import TackStatus
from group.models import Group
from tack.models import Tack


class MainConsumer(WebsocketConsumer):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def connect(self):
        # Logic to add all groups to User websocket
        # self.channel_name = self.scope['url_route']['kwargs']['user_id']
        # user = self.scope['user']
        # print(f"{user = }")
        logger = logging.getLogger()
        logger.warning(f"{self.channel_name = }")
        # if user.is_anonymous:
        #     self.close()

        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'user_{self.user_id}'

        logger.warning(f"{self.room_group_name = }")
        # Join user_id room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        # async _ to sync
        groups = Group.objects.filter(groupmembers__user=self.scope['url_route']['kwargs']['user_id'])
        for group in groups:
            async_to_sync(self.channel_layer.group_add)(
                f"group_{group.id}",
                self.channel_name
            )

        # tacks_tacker = Tack.active.filter(
        #     tacker=self.scope['url_route']['kwargs']['user_id']
        # ).exclude(
        #     status=TackStatus.FINISHED
        # )
        # for tack in tacks_tacker:
        #     async_to_sync(self.channel_layer.group_add)(
        #         f"tack_{tack.id}_tacker",
        #         self.channel_name
        #     )

        # tacks_runner = Tack.active.filter(
        #     tacker=self.scope['url_route']['kwargs']['user_id']
        # ).exclude(
        #     status=TackStatus.FINISHED
        # )
        # for tack in tacks_runner:
        #     async_to_sync(self.channel_layer.group_add)(
        #         f"tack_{tack.id}_runner",
        #         self.channel_name
        #     )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def tack_create(self, event):
        message = event['message']

        logging.getLogger().warning(f"In tack_create : {event = }")
        self.channel_layer.group_add(
            f"tack_{message['id']}_tacker",
            self.channel_name
        )

        self.send(
            text_data=json.dumps(
                {
                    'model': 'Tack',
                    'action': 'create',
                    'message': message
                }
            ))

    def balance_update(self, event):
        message = event['message']
        logging.getLogger().warning(f"In balance_update : {event = }")
        self.send(
            text_data=json.dumps(
                {
                    'model': 'Balance',
                    'action': 'update',
                    'message': message
                }
            ))
