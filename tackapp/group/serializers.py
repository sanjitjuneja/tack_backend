from rest_framework import serializers

from user.models import User
from .models import *


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = "id", "owner", "name", "description", "image", "is_public"
        read_only_fields = "owner",


class GroupInvitationsSerializer(serializers.ModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = GroupInvitations
        fields = "__all__"


class GroupInvitationsPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInvitations
        fields = "__all__"


class UserInviteSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())


class GroupInviteLinkSerializer(serializers.Serializer):
    uuid = serializers.CharField(max_length=36, required=True)


class GroupMembersSerializer(serializers.ModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = GroupMembers
        fields = "id", "group", "is_muted"
