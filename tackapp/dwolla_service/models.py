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


# class DwollaPaymentMethod(models.Model):
#     bank_account_type = models.CharField(max_length=64)
#     bank_name = models.CharField(max_length=128)
#     channels = models.JSONField()
#     created = models.DateTimeField()
#     fingerprint = models.CharField(max_length=64)
#     source_id = models.UUIDField()
#     name = models.CharField(max_length=128)
#     removed = models.BooleanField(default=False)
#     status = models.CharField(max_length=32)
#     source_type = models.CharField(max_length=32)
#
#     class Meta:
#         db_table = "dwolla_payment_methods"
#         verbose_name = "Dwolla Payment method"
#         verbose_name_plural = "Dwolla Payment methods"
