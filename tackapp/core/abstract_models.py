from django.db import models


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class CoreModel(models.Model):
    is_active = models.BooleanField(default=True)
    creation_time = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    active = ActiveManager()

    def delete(self, using=None, keep_parents=False):
        self.is_active = False
        self.save()

    class Meta:
        abstract = True
