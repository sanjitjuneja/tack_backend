from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Tack, Offer, PopularTack


@admin.register(Tack)
class TackAdmin(ModelAdmin):
    list_display = ['id', 'tacker', 'runner', 'status', 'title', 'price', 'allow_counter_offer']
    list_filter = ['allow_counter_offer', 'status']


@admin.register(PopularTack)
class PopularTacksAdmin(ModelAdmin):
    list_display = ['id', 'title', 'tacker', 'price', 'allow_counter_offer']
    list_display_links = ['title']
    list_filter = ['allow_counter_offer', 'group']


@admin.register(Offer)
class OfferAdmin(ModelAdmin):
    list_display = ['id', 'tack', 'runner', 'offer_type', 'is_accepted', 'creation_time']
    list_filter = ['offer_type', 'is_accepted']
