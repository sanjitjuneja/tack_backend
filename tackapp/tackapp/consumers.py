import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q

from core.choices import TackStatus
from group.models import Group, GroupMembers
from tack.models import Tack
from tackapp.services import form_websocket_message


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
        group_members = GroupMembers.objects.filter(member=self.scope['url_route']['kwargs']['user_id'])
        for gm in group_members:
            async_to_sync(self.channel_layer.group_add)(
                f"group_{gm.group.id}",
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
        # TODO: leave all groups
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
            text_data=form_websocket_message(
                model='Tack', action='create', obj=message
            ))

    def balance_update(self, event):
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='Balance', action='update', obj=message
            ))

    def invitation_create(self, event):
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='GroupInvitation', action='create', obj=message
            ))

    def user_update(self, event):
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='User', action='update', obj=message
            ))

    def group_create(self, event):
        message = event['message']
        async_to_sync(self.channel_layer.group_add)(
            f"group_{message.id}",
            self.channel_name)

        self.send(
            text_data=form_websocket_message(
                model='Group', action='create', obj=message
            )
        )
