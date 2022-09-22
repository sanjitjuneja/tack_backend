from rest_framework import serializers

from core.custom_serializers import CustomModelSerializer, CustomSerializer
from user.models import User
from .models import *


class GroupSerializer(CustomModelSerializer):

    class Meta:
        model = Group
        fields = "id", "owner", "name", "description", "image", "is_public"
        read_only_fields = "owner",


class GroupInvitationsSerializer(CustomModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = GroupInvitations
        fields = "__all__"


class GroupInvitationsPostSerializer(CustomModelSerializer):
    class Meta:
        model = GroupInvitations
        fields = "__all__"


class UserInviteSerializer(CustomSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())


class GroupInviteLinkSerializer(CustomSerializer):
    uuid = serializers.CharField(max_length=36, required=True)


class GroupMembersSerializer(CustomModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = GroupMembers
        fields = "id", "group", "is_muted"
