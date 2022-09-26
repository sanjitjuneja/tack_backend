import logging

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from tackapp.websocket_messages import WSSender
from .models import Group, GroupMembers, GroupInvitations
from .serializers import GroupInvitationsSerializer, GroupMembersSerializer


ws_sender = WSSender()
logger = logging.getLogger('django')
logger.warning(f"in Group signals {ws_sender = }")


@receiver(signal=post_save, sender=Group)
def set_owner_as_group_member(instance: Group, created: bool, *args, **kwargs):
    if created:
        GroupMembers.objects.create(group=instance, member=instance.owner)


@receiver(signal=post_save, sender=GroupInvitations)
def post_save_invitations(instance: GroupInvitations, *args, **kwargs):
    logger.warning("post_save_invitations")
    logger.warning(f"{instance = }")
    ws_sender.send_message(
        f"user_{instance.invitee_id}",
        'invitation.create',
        GroupInvitationsSerializer(instance).data)


@receiver(signal=post_delete, sender=GroupInvitations)
def post_delete_invitations(instance: GroupInvitations, *args, **kwargs):
    ws_sender.send_message(
        f"user_{instance.invitee.id}",
        'invitation.delete',
        instance.id)


@receiver(signal=post_save, sender=GroupMembers)
def post_save_group_members(instance: GroupMembers, created: bool, *args, **kwargs):
    if created:
        logger.warning(f"in post_save_group_members: {instance = }")
        ws_sender.send_message(
            f"user_{instance.member.id}",
            'groupdetails.create',
            GroupMembersSerializer(instance).data)
    else:
        ws_sender.send_message(
            f"user_{instance.member.id}",
            'groupdetails.update',
            GroupMembersSerializer(instance).data)


@receiver(signal=post_delete, sender=GroupMembers)
def post_delete_group_members(instance: GroupMembers, *args, **kwargs):
    ws_sender.send_message(
        f"user_{instance.member.id}",
        'groupdetails.delete',
        instance.id)
    # set another active group if user leaving his current active group


@receiver(signal=pre_delete, sender=GroupMembers)
def pre_delete_group_members(instance: GroupMembers, *args, **kwargs):
    logging.getLogger().warning(f"{instance = }")
    logging.getLogger().warning(f"{instance.group = }")
    logging.getLogger().warning(f"{instance.member.active_group = }")
    if instance.member.active_group == instance.group:
        recent_gm = GroupMembers.objects.filter(
            member=instance.member
        ).exclude(
            id=instance.id
        ).last()
        logging.getLogger().warning(f"{recent_gm = }")
        recent_group = recent_gm.group if recent_gm else None
        instance.member.active_group = recent_group
        instance.member.save()
