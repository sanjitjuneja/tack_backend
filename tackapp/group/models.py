from datetime import datetime
from uuid import uuid4

from django.db import models
from django.db.models import UniqueConstraint

from core.abstract_models import CoreModel


def upload_path_group_image(instance, filename: str):
    extension = filename.split(".")[-1]
    today = datetime.today()
    year, month = today.year, today.month
    return f"groups/{year}/{month}/{uuid4()}.{extension}"


class Group(CoreModel):
    owner = models.ForeignKey("user.User", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=256, null=True, blank=True)
    image = models.ImageField(
        null=True, blank=True, upload_to=upload_path_group_image
    )
    is_public = models.BooleanField(default=False)
    invitation_link = models.CharField(max_length=36, unique=True, default=uuid4)
    # members_count

    # def save(self, *args, **kwargs):
    #     self.invitation_link = uuid4()
    #     super(Group, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}: {self.name}"

    class Meta:
        db_table = "groups"
        verbose_name = "Group"
        verbose_name_plural = "Groups"


class GroupMembers(models.Model):
    group = models.ForeignKey("group.Group", on_delete=models.CASCADE)
    member = models.ForeignKey("user.User", on_delete=models.CASCADE)

    class Meta:
        db_table = "group_membership"
        verbose_name = "Group membership"
        verbose_name_plural = "Groups membership"
        constraints = [
            UniqueConstraint(fields=['group', 'member'], name='unique_member_for_group')
        ]


class GroupInvitations(CoreModel):
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


class GroupMutes(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE)
    group = models.ForeignKey("group.Group", on_delete=models.CASCADE)

    class Meta:
        db_table = "group_mutes"
        verbose_name = "Group mute"
        verbose_name_plural = "Group mutes"
