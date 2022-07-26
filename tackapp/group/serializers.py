from rest_framework import serializers

from user.models import User
from user.serializers import UserSerializer
from .models import *


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "id", "owner", "name", "description", "image", "is_public"
        read_only_fields = "owner",


class GroupMembersSerializer(serializers.ModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = GroupMembers
        fields = "group",
        read_only_fields = "group",

# class GroupMembersSerializer(serializers.ModelSerializer):
#     data = serializers.SerializerMethodField()
#
#     def get_data(self, obj: GroupMembers):
#         return {
#             "group": {
#                 obj.group.id,
#                 obj.group.owner.id,
#                 obj.group.name,
#                 obj.group.description,
#                 obj.group.image,
#                 obj.group.is_public
#             }
#         }
#
#     class Meta:
#         model = GroupMembers
#         fields = "group", "data"
#         read_only_fields = "group", "data"


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
