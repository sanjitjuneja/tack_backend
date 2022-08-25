from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import *


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_display = ['name', 'owner', 'description', 'is_public']
    list_filter = ['is_public']
    search_fields = ("name__contains",)


@admin.register(GroupMembers)
class GroupMembersAdmin(ModelAdmin):
    list_display = ['id', 'group', 'member', 'is_muted']
    list_filter = ['group']


@admin.register(GroupInvitations)
class GroupInvitationsAdmin(ModelAdmin):
    list_display = ['id', 'group', 'invitee']
    list_filter = ['group']


# @admin.register(GroupMutes)
# class GroupMutesAdmin(ModelAdmin):
#     list_display = ['id', 'group', 'user']
#     list_filter = ['group']

