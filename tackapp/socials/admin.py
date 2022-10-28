from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import PhoneVerification, TimeoutSettings, FailedLoginAttempts, NotificationSettings


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('uuid', 'user', 'phone_number', 'sms_code', 'sms_type', 'is_verified')
    search_fields = ("uuid", "user", "user__firstname", "user__lastname", "sms_code")
    search_help_text = "Search by uuid;, User id, name; sms code"


@admin.register(FailedLoginAttempts)
class FailedLoginAttemptsAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('credentials', 'device_id', 'user', 'device_type', 'device_name', 'timestamp')
    search_fields = ("credentials", "device_id", "user", "user__firstname", "user_lastname", "device_name")
    search_help_text = "Search by Credentials; Device id, name; User id, name"


@admin.register(TimeoutSettings)
class TimeoutSettingsAdmin(ModelAdmin):
    list_display = (
        'signup_time_window_minutes',
        'signup_max_attempts_per_window',
        'signup_activation_code_ttl_minutes',
        'signin_time_window_minutes',
        'signin_max_attempts_per_window'
    )


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(ModelAdmin):
    list_display = ('type', 'title_template', 'body_template')
