from uuid import uuid4

from django.db import models


class Group(models.Model):
    owner = models.ForeignKey("user.User", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=256, null=True, blank=True)
    image = models.ImageField(
        null=True, blank=True, upload_to="static/media/group_images/"
    )
    is_public = models.BooleanField(default=False)
    invitation_link = models.CharField(max_length=36, default=uuid4())
    creation_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        db_table = "groups"
        verbose_name = "Group"
        verbose_name_plural = "Groups"
