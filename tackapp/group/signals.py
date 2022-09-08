from uuid import uuid4

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Group, GroupMembers, GroupInvitations
from .serializers import GroupInvitationsSerializer


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
