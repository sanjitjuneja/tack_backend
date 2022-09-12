import logging
from uuid import uuid4

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from tackapp.websocket_messages import WSSender
from .models import Group, GroupMembers, GroupInvitations
from .serializers import GroupInvitationsSerializer, GroupSerializer, GroupMembersSerializer


ws_sender = WSSender()


@receiver(signal=post_save, sender=Group)
def set_owner_as_group_member(instance: Group, created: bool, *args, **kwargs):
    if created:
        GroupMembers.objects.create(group=instance, member=instance.owner)


@receiver(signal=post_save, sender=GroupInvitations)
def post_save_invitations(instance: GroupInvitations, *args, **kwargs):
    ws_sender.send_message(
        f"user_{instance.invitee.id}",
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
        instance.group.id)
    # set another active group if user leaving his current active group


@receiver(signal=pre_delete, sender=GroupMembers)
def pre_delete_group_members(instance: GroupMembers, *args, **kwargs):
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
