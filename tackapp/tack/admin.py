from django.contrib.admin import ModelAdmin

from django.contrib import admin
from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.db.models import Count

from core.choices import TackStatus
from .models import Tack, Offer, PopularTack


@admin.register(Tack)
class TackAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    list_per_page = 50
    list_display = ['id', 'title', 'price', 'tacker', 'runner', 'status', 'num_offers', 'allow_counter_offer', 'group', 'creation_time']
    list_display_links = ("title",)
    list_filter = ['allow_counter_offer', 'status', 'creation_time']
    advanced_filter_fields = (
        'status',
    )
    search_fields = (
        "tack__title",
        "tacker__first_name",
        "tacker__last_name",
        "runner__first_name",
        "runner__last_name",
        "group__name",
        "group__id",
    )
    search_help_text = "Search by Tack title, Tacker name, Runner name, Group id, name"
    ordering = ('-id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _num_offers=Count("offer", distinct=True),
        )
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        parent_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "accepted_offer":
            kwargs["queryset"] = Offer.active.filter(tack_id=parent_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.action(description='Cancel selected Tacks')
    def cancel_tacks(self, request, queryset):
        if queryset.count() == queryset.filter(status_in=(TackStatus.CREATED, TackStatus.ACTIVE)).count():
            queryset.update(is_active=False, is_canceled=True)

    @admin.display(description="Offer count")
    def num_offers(self, obj) -> int:
        return Offer.objects.filter(tack_id=obj.id).count()
    num_offers.admin_order_field = '_num_offers'


@admin.register(PopularTack)
class PopularTacksAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ['id', 'title', 'group', 'price', 'allow_counter_offer']
    list_display_links = ("title",)
    list_filter = ['allow_counter_offer', 'group']
    search_fields = ("title", "group__name")
    search_help_text = "Search by Title; Group name"
    ordering = ('-id',)


@admin.register(Offer)
class OfferAdmin(ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        parent_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "tack":
            kwargs["queryset"] = Tack.active.filter(
                tack_id=parent_id
            ) if parent_id else \
                Tack.active.filter(
                    status__in=(
                        TackStatus.CREATED,
                        TackStatus.ACTIVE
                    )
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    list_per_page = 50
    list_display = ['id', 'view_offer_str', 'status', 'is_active', 'offer_type', 'price']
    list_display_links = ("view_offer_str",)
    list_filter = ['offer_type', 'is_active', 'status']
    search_fields = ['id', 'title', 'description', 'tack__title', 'runner__firstname', 'runner__lastname']
    search_help_text = "Search by Offer id, title, description; Tack title; Runner name"
    ordering = ('-id',)

    @admin.display(description="Description")
    def view_offer_str(self, obj) -> str:
        return str(obj)
