import unicodedata

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth import password_validation
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, ReadOnlyPasswordHashField
from django.forms import forms, CharField, ModelForm
from django.contrib.sessions.models import Session

from .models import *
from django.utils.translation import gettext_lazy as _


class CustomUserCreationForm(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.username = user.phone_number.as_e164[1:]
        if commit:
            user.save()
        return user

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('phone_number',)


class CustomUserChangeForm(UserChangeForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('phone_number',)


class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = (
        "id", "phone_number", "email", "first_name", "last_name",
        "is_staff", "username",
    )
    list_display_links = "phone_number",
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        (_("Personal info"), {"fields": (
            "username", "first_name", "last_name", "email",
            "profile_picture", "birthday")}
         ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', "first_name", "last_name"),
        }),
    )
    ordering = ("id",)


class SessionAdmin(ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()
    list_display = ['session_key', '_session_data', 'expire_date']


admin.site.register(User, CustomUserAdmin)
admin.site.register(Session, SessionAdmin)
