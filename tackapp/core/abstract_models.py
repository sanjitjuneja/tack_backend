from django.db import models


class CoreModel(models.Model):
    is_active = models.BooleanField(default=True)
    creation_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
