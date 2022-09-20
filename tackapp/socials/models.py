from django.db import models
from django.db.models import UniqueConstraint
from phonenumber_field.modelfields import PhoneNumberField

from core.abstract_models import CoreModel
from core.choices import SMSType, NotificationType


class PhoneVerification(CoreModel):
    uuid = models.CharField(max_length=36)
    user = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, blank=True, null=True
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


class FailedLoginAttempts(models.Model):
    device_id = models.CharField(max_length=128, null=True, blank=True, default=None)
    device_type = models.CharField(max_length=128, null=True, blank=True, default=None)
    device_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    user = models.ForeignKey('user.User', null=True, blank=True, default=None, on_delete=models.SET_NULL)
    credentials = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "failed_login_attempts"
        verbose_name = "Failed login attempt"
        verbose_name_plural = "Failed login attempts"


class TimeoutSettings(models.Model):
    signup_time_window_minutes = models.PositiveSmallIntegerField(default=60)
    signup_max_attempts_per_window = models.PositiveSmallIntegerField(default=3)
    signup_activation_code_ttl_minutes = models.PositiveSmallIntegerField(default=360)
    signin_time_window_minutes = models.PositiveSmallIntegerField(default=60)
    signin_max_attempts_per_window = models.PositiveSmallIntegerField(default=10)

    class Meta:
        db_table = "timeout_settings"
        verbose_name = "Timeout setting"
        verbose_name_plural = "Timeout settings"


class NotificationSettings(models.Model):
    type = models.CharField(max_length=32, choices=NotificationType.choices)
    title_template = models.TextField(max_length=100, null=True, blank=True)
    body_template = models.TextField(max_length=256, null=True, blank=True)

    class Meta:
        db_table = "notification_settings"
        verbose_name = "Notification settings"
        verbose_name_plural = "Notification settings"
        constraints = [
            UniqueConstraint(
                fields=('type',),
                name='unique_type_for_settings'
            )
        ]
