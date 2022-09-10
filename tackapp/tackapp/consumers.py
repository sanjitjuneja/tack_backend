import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q

from core.choices import TackStatus
from group.models import Group, GroupMembers
from group.serializers import GroupSerializer
from tack.models import Tack, Offer
from tackapp.services import form_websocket_message

logger = logging.getLogger()


class MainConsumer(WebsocketConsumer):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    def connect(self):
        self.user = self.scope['user']
        logger = logging.getLogger()
        logger.warning(f"WS connected {self.user}")
        logger.warning(f"{self.channel_name = }")
        if self.user.is_anonymous:
            self.close()

        self.room_group_name = f'user_{self.user.id}'

        logger.warning(f"{self.room_group_name = }")
        # Join user_id room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name)

        # async _ to sync
        group_members = GroupMembers.objects.filter(member=self.user)
        for gm in group_members:
            async_to_sync(self.channel_layer.group_add)(
                f"group_{gm.group.id}",
                self.channel_name
            )
            logger.warning(f"{gm = }")
            logger.warning(f"group_{gm.group.id}")

        tacks_tacker = Tack.active.filter(
            tacker=self.user
        ).exclude(
            status=TackStatus.FINISHED
        )
        for tack in tacks_tacker:
            async_to_sync(self.channel_layer.group_add)(
                f"tack_{tack.id}_tacker",
                self.channel_name
            )
            logger.warning(f"tack_{tack.id}_tacker")

        tacks_runner = Tack.active.filter(
            runner=self.user
        ).exclude(
            status=TackStatus.FINISHED
        )
        for tack in tacks_runner:
            async_to_sync(self.channel_layer.group_add)(
                f"tack_{tack.id}_runner",
                self.channel_name
            )
            logger.warning(f"tack_{tack.id}_runner")

        offers = Offer.active.filter(
            runner=self.user
        ).select_related(
            "tack"
        )
        for offer in offers:
            async_to_sync(self.channel_layer.group_add)(
                f"tack_{offer.tack.id}_offer",
                self.channel_name
            )
            logger.warning(f"tack_{offer.tack.id}_offer")
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        # TODO: leave all groups
        logger.warning(f"{close_code = }")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def tack_create(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.channel_layer.group_add(
            f"tack_{message['id']}_tacker",
            self.channel_name
        )
        logging.getLogger().warning(f"in tack_create: tack_{message['id']}_tacker",)
        self.send(
            text_data=form_websocket_message(
                model='Tack', action='create', obj=message
            ))

    def tack_update(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='Tack', action='update', obj=message
            ))

    def tack_delete(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        async_to_sync(self.channel_layer.group_discard)(
            f"tack_{message}_tacker",
            self.channel_name)
        async_to_sync(self.channel_layer.group_discard)(
            f"tack_{message}_offer",
            self.channel_name)
        self.send(
            text_data=form_websocket_message(
                model='Tack', action='delete', obj=message
            )
        )

    def grouptack_create(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='GroupTack', action='create', obj=message
            ))

    def grouptack_update(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='GroupTack', action='update', obj=message
            ))

    def grouptack_delete(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='GroupTack', action='delete', obj=message
            ))

    def balance_update(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='Balance', action='update', obj=message
            ))

    def invitation_create(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='GroupInvitation', action='create', obj=message
            ))

    def invitation_delete(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='GroupInvitation', action='delete', obj=message
            ))

    def user_update(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='User', action='update', obj=message
            ))

    def groupdetails_create(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        async_to_sync(self.channel_layer.group_add)(
            f"group_{message['id']}",
            self.channel_name)
        logging.getLogger().warning(f"Added to group_{message['id']}")
        self.send(
            text_data=form_websocket_message(
                model='GroupDetails', action='create', obj=message
            )
        )

    def groupdetails_update(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='GroupDetails', action='update', obj=message
            )
        )

    def groupdetails_delete(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        async_to_sync(self.channel_layer.group_discard)(
            f"group_{message}",
            self.channel_name)
        self.send(
            text_data=form_websocket_message(
                model='GroupDetails', action='delete', obj=message
            )
        )

    def offer_create(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='Offer', action='create', obj=message
            )
        )

    def offer_delete(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        self.send(
            text_data=form_websocket_message(
                model='Offer', action='delete', obj=message
            )
        )

    def runnertack_create(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        async_to_sync(self.channel_layer.group_add)(
            f"tack_{message['id']}_offer",
            self.channel_name)
        self.send(
            text_data=form_websocket_message(
                model='RunnerTack', action='create', obj=message
            )
        )

    def runnertack_update(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        async_to_sync(self.channel_layer.group_add)(
            f"tack_{message['id']}_offer",
            self.channel_name)
        self.send(
            text_data=form_websocket_message(
                model='RunnerTack', action='update', obj=message
            )
        )

    def runnertack_delete(self, event):
        logger.warning(f"{event = }")
        message = event['message']
        async_to_sync(self.channel_layer.group_discard)(
            f"tack_{message}_offer",
            self.channel_name)
        self.send(
            text_data=form_websocket_message(
                model='RunnerTack', action='delete', obj=message
            )
        )
