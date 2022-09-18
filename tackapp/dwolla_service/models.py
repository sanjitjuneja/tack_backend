from django.db import models


class DwollaEvent(models.Model):
    event_id = models.UUIDField()
    topic = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    self_res = models.JSONField(blank=True, null=True)
    account = models.JSONField(blank=True, null=True)
    resource = models.JSONField(blank=True, null=True)
    customer = models.JSONField(blank=True, null=True)
    created = models.DateTimeField()

    class Meta:
        db_table = "dwolla_events"
        verbose_name = "Dwolla event"
        verbose_name_plural = "Dwolla events"


class DwollaRemovedAccount(models.Model):
    dwolla_id = models.UUIDField()
    creation_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dwolla_removed_accounts"
        verbose_name = "Dwolla removed account"
        verbose_name_plural = "Dwolla removed accounts"
