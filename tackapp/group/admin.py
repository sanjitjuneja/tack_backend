from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import *


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ['name', 'owner', 'description', 'is_public']
    list_filter = ['is_public']
    search_fields = ("name", "id", "owner__firstname", "owner_lastname")
    search_help_text = "Search by Group name, id, Owner name"
    ordering = ('id',)


@admin.register(GroupMembers)
class GroupMembersAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ['id', 'group', 'member', 'is_muted']
    list_filter = ['group']
    search_fields = ('id', 'member')
    search_help_text = "Search by Group id, Member id"
    ordering = ('id',)


@admin.register(GroupInvitations)
class GroupInvitationsAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ['id', 'group', 'invitee']
    list_filter = ['group']
    search_fields = ('group', 'invitee')
    search_help_text = "Search by Group id, Invitee id"
    ordering = ('id',)
