import json

from channels.db import database_sync_to_async

from core.choices import TackStatus
from group.models import GroupMembers, Group
from tack.models import Tack, Offer
from user.models import User


def form_websocket_message(*, model: str, action: str, obj: dict) -> str:
    template = {
        'model': model,
        'message': {
            'action': action
            # 'id': '',
            # 'object': ''
        }
    }
    if action == 'delete':
        template['message']['id'] = obj
        template['message']['object'] = None
    else:
        template['message']['id'] = obj['id']
        template['message']['object'] = obj

    response = json.dumps(template)
    return response


@database_sync_to_async
def get_user_groups(user: User):
    return list(GroupMembers.objects.filter(member=user).select_related("group"))


@database_sync_to_async
def get_tacks_tacker(user: User):
    tacks_tacker = Tack.active.filter(
            tacker=user
        ).exclude(
            status=TackStatus.FINISHED
        )
    return list(tacks_tacker)


@database_sync_to_async
def get_tacks_runner(user: User):
    tacks_runner = Tack.active.filter(
            runner=user
        ).exclude(
            status=TackStatus.FINISHED
        )
    return list(tacks_runner)


@database_sync_to_async
def get_user_offers(user: User):
    offers = Offer.active.filter(
            runner=user
        ).select_related(
            "tack"
        )
    return list(offers)
