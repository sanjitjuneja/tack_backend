from advanced_filters.admin import AdminAdvancedFiltersMixin
from stats.models import GlobalStats, GroupStats, UserVisits
from django.contrib.admin import ModelAdmin
from payment.admin import ReadOnlyMixin
from django.contrib import admin


@admin.register(GlobalStats)
class GlobalStatsAdmin(AdminAdvancedFiltersMixin, ReadOnlyMixin, ModelAdmin):
    pass


@admin.register(GroupStats)
class GroupStatsAdmin(AdminAdvancedFiltersMixin, ReadOnlyMixin, ModelAdmin):
    pass


@admin.register(UserVisits)
class UserVisitsAdmin(ModelAdmin):

    @admin.display(description="User")
    def get_user_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"

    list_display = [
        'get_user_name',
        'timestamp',
    ]