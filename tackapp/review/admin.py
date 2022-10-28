from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import *


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('id', 'user', 'tack', 'rating', 'description')
    list_filter = ('rating',)
    readonly_fields = ('creation_time',)
    search_fields = ('user', 'user__firstname', 'user__lastname', 'tack', 'tack__title')
    search_help_text = "Search by User id, name; Tack id, title"
