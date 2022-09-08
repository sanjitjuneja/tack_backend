from uuid import uuid4

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Group, GroupMembers, GroupInvitations
from .serializers import GroupInvitationsSerializer, GroupSerializer, GroupMembersSerializer


@receiver(signal=post_save, sender=Group)
def set_owner_as_group_member(instance: Group, created: bool, *args, **kwargs):
    if created:
        GroupMembers.objects.create(group=instance, member=instance.owner)


@receiver(signal=post_save, sender=GroupInvitations)
def post_save_invitations(instance: GroupInvitations, *args, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{instance.invitee.id}",
        {
            'type': 'invitation.create',
            'message': GroupInvitationsSerializer(instance).data
        })


@receiver(signal=post_delete, sender=GroupInvitations)
def post_delete_invitations(instance: GroupInvitations, *args, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{instance.invitee.id}",
        {
            'type': 'invitation.delete',
            'message': instance.id
        })


@receiver(signal=post_save, sender=GroupMembers)
def post_save_group_members(instance: GroupMembers, *args, **kwargs):
    channel_layer = get_channel_layer()
    gm = GroupMembers.objects.get(group=instance)
    async_to_sync(channel_layer.group_send)(
        f"user_{instance.member.id}",
        {
            'type': 'group.create',
            'message': GroupMembersSerializer(gm).data
        })


@receiver(signal=post_delete, sender=GroupMembers)
def post_delete_group_members(instance: GroupMembers, *args, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{instance.member.id}",
        {
            'type': 'group.delete',
            'message': instance.group.id
        })
