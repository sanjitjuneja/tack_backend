from rest_framework import viewsets, parsers
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import GroupOwnerPermission, GroupMemberPermission
from .serializers import *


class GroupViewset(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (GroupOwnerPermission,)
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)

    @action(methods=["GET"], detail=False, serializer_class=GroupMembersSerializer)
    def me(self, request, *args, **kwargs):
        """Endpoint for get all User's groups he is member of"""

        qs = GroupMembers.objects.filter(member=request.user).select_related("group")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(
        methods=["POST"],
        detail=True,
        serializer_class=serializers.Serializer,
        permission_classes=(GroupMemberPermission,)
    )
    def set_active(self, request, *args, **kwargs):
        """Endpoint for setting active Group to the User (for further Tack creation)"""

        group = self.get_object()
        request.user.active_group = group
        request.user.save()
        serializer = GroupSerializer(group)
        return Response(serializer.data)

    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        GroupMembers.objects.create(group=group, member=self.request.user)
        # TODO: Do as a trigger? (Adding Group owner as a member of his Group)

    def perform_update(self, serializer):
        serializer.save(owner=self.request.user)
