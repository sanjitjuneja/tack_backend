from django.contrib.admin import ModelAdmin

from django.contrib import admin
from advanced_filters.admin import AdminAdvancedFiltersMixin
from .models import Tack, Offer, PopularTack


@admin.register(Tack)
class TackAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        parent_id = request.resolver_match.kwargs['object_id']
        if db_field.name == "accepted_offer":
            kwargs["queryset"] = Offer.active.filter(tack_id=parent_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_per_page = 50
    list_display = ['id', 'tacker', 'runner', 'status', 'title', 'price', 'view_num_offers', 'allow_counter_offer', 'group', 'creation_time']
    list_filter = ['allow_counter_offer', 'status', 'creation_time']
    advanced_filter_fields = (
        'status',
    )
    search_fields = ("tacker__name__contains",)
    ordering = ('-id',)

    @admin.display(description="Offer count")
    def view_num_offers(self, obj) -> int:
        return Offer.objects.filter(tack_id=obj.id).count()


@admin.register(PopularTack)
class PopularTacksAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ['id', 'title', 'group', 'price', 'allow_counter_offer']
    list_display_links = ['title']
    list_filter = ['allow_counter_offer', 'group']
    ordering = ('-id',)


@admin.register(Offer)
class OfferAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ['id', 'view_offer_str', 'status', 'is_active', 'offer_type', 'price']
    list_filter = ['offer_type', 'is_active', 'status']
    search_fields = ['id', 'title', 'description', 'runner']
    ordering = ('-id',)

    @admin.display(description="Description")
    def view_offer_str(self, obj) -> str:
        return str(obj)
