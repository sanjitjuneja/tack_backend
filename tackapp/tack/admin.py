import datetime
import logging
from datetime import timedelta

from django.contrib.admin import ModelAdmin

from django.contrib import admin
from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.utils import timezone

from core.choices import TackStatus
from payment.services import convert_to_decimal
from .models import Tack, Offer, PopularTack
from django.contrib.admin import ModelAdmin
from core.choices import TackStatus
from django.utils import timezone
from django.contrib import admin
from django.db.models import (
    Count,
    Q,
    QuerySet,
    F,
    ExpressionWrapper,
    DateTimeField,
    Case,
    When
)


class ExpiringTacksFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Expiring tacks'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'expiring_tacks'

    def lookups(self, request, model_admin):
        return (("expire_soon", "Expiring First"),)

    def to_datetime(self, seconds):
        return timedelta(seconds=seconds) + timezone.now()

    def queryset(self, request, queryset: QuerySet[Tack]):
        logger = logging.getLogger('django')
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == "expire_soon":
            expiring_tacks = queryset.filter(
                start_completion_time__isnull=False
            ).annotate(
                expiration_time=ExpressionWrapper(
                    timedelta(seconds=1) * F('estimation_time_seconds') * 0.9 + timezone.now(),
                    output_field=DateTimeField()
                )
            ).filter(
                start_completion_time__lt=F('expiration_time'),
                is_active=True
            ).exclude(
                status__in=(TackStatus.FINISHED, TackStatus.WAITING_REVIEW)
            ).order_by(
                'expiration_time'
            )
            ordering = (TackStatus.IN_PROGRESS, TackStatus.ACCEPTED, TackStatus.ACTIVE, TackStatus.CREATED)
            preserved = Case(*[When(status=status, then=pos) for pos, status in enumerate(ordering)])
            other_tacks_included = queryset.filter(
                status__in=(
                    TackStatus.CREATED,
                    TackStatus.ACTIVE,
                    TackStatus.ACCEPTED,
                    TackStatus.IN_PROGRESS
                ),
                is_active=True
            ).order_by(
                preserved
            )
            logger.info(f"{expiring_tacks.values('id', 'status', 'creation_time', 'estimation_time_seconds') = }")
            logger.info(f"{other_tacks_included.values('id', 'status', 'creation_time', 'estimation_time_seconds') = }")
            union_result = (expiring_tacks | other_tacks_included).distinct()
            logger.info(f"{union_result.values('id', 'status', 'creation_time', 'estimation_time_seconds') = }")
            return union_result
        return queryset


@admin.register(Tack)
class TackAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    list_per_page = 50
    list_display = ('id', 'title', 'human_readable_price', 'status', 'expires_at', 'is_active', 'tacker', 'runner',
                    'num_offers', 'allow_counter_offer', 'group', 'creation_time')
    list_display_links = ("title",)
    list_filter = (ExpiringTacksFilter, 'is_active', 'allow_counter_offer', 'status', 'creation_time', 'is_paid', 'group')
    readonly_fields = ('creation_time',)
    advanced_filter_fields = (
        'status',
        'price',
        'allow_counter_offer',
        'is_paid',
        'is_canceled',
    )
    search_fields = (
        "title",
        "tacker__first_name",
        "tacker__last_name",
        "runner__first_name",
        "runner__last_name",
        "group__name",
        "group__id",
    )
    search_help_text = "Search by Tack title, Tacker name, Runner name, Group id, name"
    actions = ('cancel_tacks',)
    # ordering = ('-id',)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

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
        for tack in queryset:
            tack.cancel()

    @admin.display(description="Offer count")
    def num_offers(self, obj) -> int:
        return Offer.objects.filter(tack_id=obj.id).count()

    num_offers.admin_order_field = '_num_offers'

    @admin.display(description="Price", ordering='price')
    def human_readable_price(self, obj):
        decimal_amount = convert_to_decimal(obj.price)
        if decimal_amount % 1:
            return f"${decimal_amount:.2f}"
        return f"${str(decimal_amount)}"

    @admin.display(description="Expires at")
    def expires_at(self, obj: Tack):
        if not (obj.start_completion_time and obj.estimation_time_seconds):
            return "-"
        return obj.start_completion_time + timedelta(seconds=obj.estimation_time_seconds)


@admin.register(PopularTack)
class PopularTacksAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('id', 'title', 'group', 'human_readable_price', 'allow_counter_offer')
    list_display_links = ("title",)
    list_filter = ('allow_counter_offer', 'group')
    search_fields = ("title", "group__name")
    search_help_text = "Search by Title; Group name"
    ordering = ('-id',)

    @admin.display(description="Price", ordering='price')
    def human_readable_price(self, obj):
        if not obj.price:
            return "-"
        decimal_amount = convert_to_decimal(obj.price)
        if decimal_amount % 1:
            return f"${decimal_amount:.2f}"
        return f"${str(decimal_amount)}"


@admin.register(Offer)
class OfferAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        parent_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "tack":
            if parent_id:
                kwargs["queryset"] = Tack.objects.filter(
                    offer=parent_id
                )
            else:
                kwargs["queryset"] = Tack.active.filter(
                    status__in=(
                        TackStatus.CREATED,
                        TackStatus.ACTIVE
                    ),
                    auto_accept=False
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_per_page = 50
    list_display = ('id', 'view_offer_str', 'offer_type', 'human_readable_price', 'status', 'is_active')
    list_display_links = ("view_offer_str",)
    list_filter = ('offer_type', 'is_active', 'status')
    readonly_fields = ('creation_time',)
    advanced_filter_fields = (
        'status',
        'is_active',
        'offer_type',
        'price',
    )
    search_fields = ('id', 'tack__title', 'tack__description', 'runner__first_name', 'runner__last_name')
    search_help_text = "Search by Offer id, title, description; Tack title; Runner name"
    ordering = ('-id',)

    @admin.display(description="Description")
    def view_offer_str(self, obj) -> str:
        return str(obj)

    @admin.display(description="Price", ordering='price')
    def human_readable_price(self, obj):
        price = obj.price if obj.price else obj.tack.price
        if not price:
            return "-"
        decimal_amount = convert_to_decimal(price)
        if decimal_amount % 1:
            return f"${decimal_amount:.2f}"
        return f"${str(decimal_amount)}"
