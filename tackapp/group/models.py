from datetime import datetime
from uuid import uuid4

from django.db import models
from django.db.models import UniqueConstraint
from django.utils.safestring import mark_safe

from core.abstract_models import CoreModel


def upload_path_group_image(instance, filename: str):
    extension = filename.split(".")[-1]
    today = datetime.today()
    year, month = today.year, today.month
    return f"groups/{year}/{month}/{uuid4()}.{extension}"


class Group(CoreModel):
    owner = models.ForeignKey("user.User", null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=256, null=True, blank=True)
    image = models.ImageField(
        null=True, blank=True, upload_to=upload_path_group_image
    )
    is_public = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    invitation_link = models.CharField(max_length=36, unique=True, default=uuid4)
    collect_stats = models.BooleanField(default=True)
    member_count = models.IntegerField(default=1)


    # def members_count(self):
    #     return GroupMembers.objects.filter(
    #         group_id=self.id
    #     ).count()

    @property
    def image_preview(self):
        if self.image:
            return mark_safe('<img src="{}" width="50" height="50" />'.format(self.image.url))
        return ""

    def __str__(self):
        return f"{self.id}: {self.name}"

    class Meta:
        db_table = "groups"
        verbose_name = "Group"
        verbose_name_plural = "Groups"


class GroupMembers(models.Model):
    group = models.ForeignKey("group.Group", on_delete=models.CASCADE)
    member = models.ForeignKey("user.User", null=True, blank=True, on_delete=models.SET_NULL)
    is_muted = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Group.id: {self.group_id}, User.id: {self.member_id}, is_muted: {self.is_muted}"

    class Meta:
        db_table = "group_membership"
        verbose_name = "Group membership"
        verbose_name_plural = "Groups membership"
        constraints = [
            UniqueConstraint(fields=['group', 'member'], name='unique_member_for_group')
        ]


class GroupInvitations(models.Model):
    invitee = models.ForeignKey("user.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="gi_invitee")
    group = models.ForeignKey("group.Group", on_delete=models.CASCADE)

    class Meta:
        db_table = "group_invitations"
        verbose_name = "Group invitation"
        verbose_name_plural = "Groups invitation"


class GroupTacks(models.Model):
    group = models.ForeignKey("group.Group", null=True, on_delete=models.SET_NULL)
    tack = models.ForeignKey("tack.Tack", on_delete=models.CASCADE)

    class Meta:
        db_table = "group_tacks"
        verbose_name = "Group Tack"
        verbose_name_plural = "Group Tacks"
