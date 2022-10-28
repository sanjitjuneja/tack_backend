from advanced_filters.admin import AdminAdvancedFiltersMixin
from stats.models import GlobalStats, GroupStats, UserVisits, Definitions
from django.contrib.admin import ModelAdmin

from payment.admin import ReadOnlyMixin
from django.contrib import admin


@admin.register(GlobalStats)
class GlobalStatsAdmin(AdminAdvancedFiltersMixin, ReadOnlyMixin, ModelAdmin):
    list_display = (
        "id",
        "timestamp",
        "num_tacks_created_last_hour",
        "num_tacks_accepted_last_hour",
        "num_tacks_completed_last_hour",
        "avg_first_offer_time_seconds",
    )


@admin.register(GroupStats)
class GroupStatsAdmin(AdminAdvancedFiltersMixin, ReadOnlyMixin, ModelAdmin):
    list_display = (
        "id",
        "timestamp",
        "group",
        "num_tacks_created_last_hour",
        "num_tacks_accepted_last_hour",
        "num_tacks_completed_last_hour",
        "avg_first_offer_time_seconds",
    )


@admin.register(Definitions)
class GroupStatsAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    list_display = [
        'active_user_timedelta_days',
        'amount_of_tacks_for_tacker',
        'amount_of_tacks_for_runner',
        'tack_created_last_x_days_for_tacker',
    ]


@admin.register(UserVisits)
class UserVisitsAdmin(ModelAdmin):

    @admin.display(description="User")
    def get_user_name(self, obj: UserVisits):
        return f"{obj.user}"

    list_display = [
        'get_user_name',
        'timestamp',
    ]
