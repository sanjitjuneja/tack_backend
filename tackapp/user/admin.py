from django.contrib import admin
from .models import *


class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "is_active")
    list_display_links = ("username",)
    sortable_by = "id", "username", "is_active", "email"
    search_fields = "email", "username"


admin.site.register(User, UserAdmin)
