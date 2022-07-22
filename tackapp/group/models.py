from uuid import uuid4

from django.db import models
from django.db.models import UniqueConstraint


class Group(models.Model):
    owner = models.ForeignKey("user.User", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=256, null=True, blank=True)
    image = models.ImageField(
        null=True, blank=True, upload_to="static/media/group_images/"
    )
    is_public = models.BooleanField(default=False)
    invitation_link = models.CharField(max_length=36, unique=True, default="")
    creation_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        db_table = "groups"
        verbose_name = "Group"
        verbose_name_plural = "Groups"


class GroupMembers(models.Model):
    group = models.ForeignKey("group.Group", on_delete=models.CASCADE)
    member = models.ForeignKey("user.User", on_delete=models.CASCADE)

    UniqueConstraint(fields=['group', 'member'], name='unique_member_for_group')

    class Meta:
        db_table = "group_membership"
        verbose_name = "Group membership"
        verbose_name_plural = "Groups membership"


class GroupInvitations(models.Model):
    inviter = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="gi_inviter")
    invitee = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="gi_invitee")
    group = models.ForeignKey("group.Group", on_delete=models.CASCADE)

    class Meta:
        db_table = "group_invitations"
        verbose_name = "Group invitation"
        verbose_name_plural = "Groups invitation"


class GroupTacks(models.Model):
    group = models.ForeignKey("group.Group", on_delete=models.SET_NULL, null=True)
    tack = models.ForeignKey("tack.Tack", on_delete=models.CASCADE)

    class Meta:
        db_table = "group_tacks"
        verbose_name = "Group Tack"
        verbose_name_plural = "Group Tacks"
