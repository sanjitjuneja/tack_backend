from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.contrib import admin
from django.contrib.admin import ModelAdmin

from payment.admin import ReadOnlyMixin
from stats.models import GlobalStats, GroupStats


@admin.register(GlobalStats)
class GlobalStatsAdmin(AdminAdvancedFiltersMixin, ReadOnlyMixin, ModelAdmin):
    pass


@admin.register(GroupStats)
class GroupStatsAdmin(AdminAdvancedFiltersMixin, ReadOnlyMixin, ModelAdmin):
    pass
