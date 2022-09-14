from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import PhoneVerification


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(ModelAdmin):
    list_display = ['uuid', 'user', 'phone_number', 'sms_code', 'sms_type', 'is_verified']
    search_fields = ("phone_number__contains",)
