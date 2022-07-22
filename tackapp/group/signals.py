from uuid import uuid4
from django.db.models.signals import post_init
from django.dispatch import receiver

from .models import Group


@receiver(signal=post_init, sender=Group)
def create_invitation_link(instance: Group, *args, **kwargs):
    instance.invitation_link = uuid4()
