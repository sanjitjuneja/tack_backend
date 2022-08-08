from uuid import uuid4
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Group, GroupMembers


@receiver(signal=post_save, sender=Group)
def set_owner_as_group_member(instance: Group, created: bool, *args, **kwargs):
    if created:
        GroupMembers.objects.create(group=instance, member=instance.owner)
