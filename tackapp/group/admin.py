from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import *


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('id_name', 'creator', 'description', 'collect_stats')
    list_editable = ('collect_stats',)
    list_filter = ('is_public',)
    readonly_fields = ('creation_time',)
    search_fields = ("name", "id", "owner__first_name", "owner__last_name")
    search_help_text = "Search by Group name, id, Owner name"
    ordering = ('id',)

    @admin.display(description="Creator")
    def creator(self, obj: Group) -> str:
        return str(obj.owner)

    @admin.display(description="Name")
    def id_name(self, obj: Group) -> str:
        return f"{obj.id}: {obj.name}"


@admin.register(GroupMembers)
class GroupMembersAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('id', 'group', 'member', 'is_muted')
    list_filter = ('group',)
    search_fields = ('id', 'member')
    readonly_fields = ('date_joined',)
    search_help_text = "Search by Group id, Member id"
    ordering = ('id',)


@admin.register(GroupInvitations)
class GroupInvitationsAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('id', 'group', 'invitee')
    list_filter = ('group',)
    search_fields = ('group', 'invitee')
    search_help_text = "Search by Group id, Invitee id"
    ordering = ('id',)
