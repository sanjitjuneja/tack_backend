from django.contrib import admin

# Register your models here.
from django.contrib.admin import ModelAdmin

from dwolla_service.models import DwollaEvent, DwollaRemovedAccount


@admin.register(DwollaEvent)
class DwollaEventAdmin(ModelAdmin):
    list_display = ('event_id', 'topic', 'timestamp')


@admin.register(DwollaRemovedAccount)
class DwollaRemovedAccountAdmin(ModelAdmin):
    list_display = ('dwolla_id', 'creation_time')
