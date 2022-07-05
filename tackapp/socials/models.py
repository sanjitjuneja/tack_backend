from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from core.choices import SMSType


class PhoneVerification(models.Model):
    uuid = models.CharField(max_length=36)
    user = models.ForeignKey(
        "user.User", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    phone_number = PhoneNumberField()
    sms_code = models.CharField(max_length=6)
    message_sid = models.CharField(max_length=64)
    sms_type = models.CharField(max_length=2, choices=SMSType.choices)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "verifications"
        verbose_name = "Verification"
        verbose_name_plural = "Verifications"
