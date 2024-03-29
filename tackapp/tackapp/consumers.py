import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from tackapp.services import (
    form_websocket_message,
    get_tacks_runner,
    get_user_groups,
    get_tacks_tacker,
    get_user_offers,
)


logger = logging.getLogger("debug")


class MainConsumer(AsyncWebsocketConsumer):
    async def websocket_connect(self, event):
        self.user = self.scope['user']
        self.device_info = self.scope['device_info']
        logger.info(f"WS connected for [{self.user} :: {self.device_info}]")
        if self.user.is_anonymous:
            await self.close()

        self.room_group_name = f'user_{self.user.id}'

        logger.info(f"{self.room_group_name = }")
        # Join user_id room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        logger.debug(f"[{self.user} :: {self.device_info}] Added to {self.room_group_name}")

        group_members = await get_user_groups(self.user)
        for gm in group_members:
            await self.channel_layer.group_add(
                f"group_{gm.group_id}",
                self.channel_name
            )
            logger.debug(f"[{self.user} :: {self.device_info}] Added to group_{gm.group_id}")

        tacks_tacker = await get_tacks_tacker(self.user)
        for tack in tacks_tacker:
            await self.channel_layer.group_add(
                f"tack_{tack.id}_tacker",
                self.channel_name
            )
            logger.debug(f"[{self.user} :: {self.device_info}] Added to tack_{tack.id}_tacker")

        tacks_runner = await get_tacks_runner(self.user)
        for tack in tacks_runner:
            await self.channel_layer.group_add(
                f"tack_{tack.id}_runner",
                self.channel_name
            )
            logger.debug(f"[{self.user} :: {self.device_info}] Added to tack_{tack.id}_runner")

        offers = await get_user_offers(self.user)
        for offer in offers:
            await self.channel_layer.group_add(
                f"tack_{offer.tack_id}_offer",
                self.channel_name
            )
            logger.debug(f"[{self.user} :: {self.device_info}] Added to tack_{offer.tack_id}_offer")
        await self.accept()

    async def websocket_receive(self, message):
        logger.debug(f"Received from [{self.user} :: {self.device_info}] :: [{message['text']}]")

    async def disconnect(self, close_code):
        # Leave room group
        # TODO: leave all groups
        logger.info(f"Disconnected {self.user} with {close_code = }")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.debug(f"[{self.user} :: {self.device_info}] Discarded [{self.room_group_name}]")

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        logger.debug(f"{message = }")

    async def tack_create(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='Tack', action='create', obj=message
            ))
        await self.channel_layer.group_add(
            f"tack_{message['id']}_tacker",
            self.channel_name
        )
        logger.debug(f"{self.user} Added to tack_{message['id']}_tacker")

    async def tack_update(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='Tack', action='update', obj=message
            ))

    async def tack_delete(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='Tack', action='delete', obj=message
            )
        )
        await self.channel_layer.group_discard(
            f"tack_{message}_tacker",
            self.channel_name)
        logger.debug(f"{self.user} Discarded to tack_{message}_tacker")
        await self.channel_layer.group_discard(
            f"tack_{message}_offer",
            self.channel_name)
        logger.debug(f"{self.user} Discarded to tack_{message}_offer")

    async def grouptack_create(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='GroupTack', action='create', obj=message
            ))

    async def grouptack_update(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='GroupTack', action='update', obj=message
            ))

    async def grouptack_delete(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='GroupTack', action='delete', obj=message
            ))

    async def balance_update(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='Balance', action='update', obj=message
            ))

    async def invitation_create(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='GroupInvitation', action='create', obj=message
            ))

    async def invitation_delete(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='GroupInvitation', action='delete', obj=message
            ))

    async def user_update(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='User', action='update', obj=message
            ))

    async def groupdetails_create(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='GroupDetails', action='create', obj=message
            )
        )
        await self.channel_layer.group_add(
            f"group_{message['id']}",
            self.channel_name)
        logger.debug(f"{self.user} Added to group_{message['id']}")

    async def groupdetails_update(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='GroupDetails', action='update', obj=message
            )
        )

    async def groupdetails_delete(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='GroupDetails', action='delete', obj=message
            )
        )
        await self.channel_layer.group_discard(
            f"group_{message}",
            self.channel_name)
        logger.debug(f"{self.user} Discarded to group_{message}")

    async def offer_create(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='Offer', action='create', obj=message
            )
        )

    async def offer_delete(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='Offer', action='delete', obj=message
            )
        )

    async def runnertack_create(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='RunnerTack', action='create', obj=message
            )
        )
        await self.channel_layer.group_add(
            f"tack_{message['id']}_offer",
            self.channel_name)
        logger.debug(f"{self.user} Added to tack_{message['id']}_offer")

    async def runnertack_update(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']

        await self.send(
            text_data=form_websocket_message(
                model='RunnerTack', action='update', obj=message
            )
        )

    async def runnertack_delete(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='RunnerTack', action='delete', obj=message
            )
        )
        await self.channel_layer.group_discard(
            f"tack_{message}_offer",
            self.channel_name)
        logger.debug(f"{self.user} Discarded to tack_{message}_offer")

    async def completedtackrunner_create(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='CompletedTackRunner', action='create', obj=message
            )
        )

    async def canceltackertackrunner_create(self, event):
        logger.debug(f"Sent to {self.user}({self.device_info}) - {event = }")
        message = event['message']
        await self.send(
            text_data=form_websocket_message(
                model='CancelTackerTackRunner', action='create', obj=message
            )
        )
