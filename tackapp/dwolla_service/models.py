from django.db import models


class DwollaEvent(models.Model):
    event_id = models.UUIDField()
    topic = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    self_res = models.JSONField()
    account = models.JSONField()
    resource = models.JSONField()
    customer = models.JSONField()
    created = models.DateTimeField()

    class Meta:
        db_table = "dwolla_events"
        verbose_name = "Dwolla event"
        verbose_name_plural = "Dwolla events"
