from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, parsers, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.choices import TackStatus
from core.permissions import GroupOwnerPermission, GroupMemberPermission, InviteePermission
from tack.models import Tack
from tack.serializers import TackDetailSerializer
from .serializers import *
from .services import get_tacks_by_group


class GroupViewset(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (GroupOwnerPermission,)
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)

    @action(methods=["GET"], detail=False)
    def me(self, request, *args, **kwargs):
        """Endpoint for get all User's groups he is member of"""

        qs = Group.objects.filter(groupmembers__member=request.user).distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

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

    @extend_schema(
        request=GroupInviteLinkSerializer,
        responses={200: GroupInvitationsSerializer, 404: {"message": "text"}},
        parameters=[
            OpenApiParameter(name='uuid', location=OpenApiParameter.QUERY, description='Group unique id',
                             required=True, type=OpenApiTypes.UUID),
        ],
    )
    @action(
        methods=["GET"],
        detail=False,
        serializer_class=GroupInviteLinkSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def invite(self, request, *args, **kwargs):
        """Endpoint for accepting invitation from Invitation Link"""

        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        uuid = serializer.validated_data["uuid"]
        try:
            group = self.get_queryset().get(invitation_link=uuid)
        except ObjectDoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        invite, created = GroupInvitations.objects.get_or_create(invitee=request.user, group=group)
        invite_serializer = GroupInvitationsSerializer(invite)
        return Response(invite_serializer.data)

    @extend_schema(responses={"message"})
    @action(methods=["POST"], detail=True, permission_classes=(GroupMemberPermission,),
            serializer_class=serializers.Serializer)
    def leave(self, request, *args, **kwargs):
        """Endpoint for leaving Group"""

        group = self.get_object()
        try:
            gm = GroupMembers.objects.get(member=request.user, group=group)
            if request.user.active_group == group:
                request.user.active_group = None
                request.user.save()
            gm.delete()
        except ObjectDoesNotExist:
            return Response({"message": "You are not a member of this group"}, status=400)

        return Response({"message": "Leaved Successfully"})

    @action(methods=["GET"], detail=True, serializer_class=TackDetailSerializer,
            permission_classes=(GroupMemberPermission,))
    def tacks(self, request, *args, **kwargs):
        """Endpoint for getting *created* and *active* Tacks of certain Group"""

        group = self.get_object()
        tacks = Tack.objects.filter(group=group, status__in=[TackStatus.created, TackStatus.active]).select_related("tacker", "runner", "group")
        page = self.paginate_queryset(tacks)
        serializer = TackDetailSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=["GET"], detail=True, serializer_class=UserListSerializer, permission_classes=(GroupMemberPermission,))
    def members(self, request, *args, **kwargs):
        group = self.get_object()
        users_qs = User.objects.filter(groupmembers__group=group)
        page = self.paginate_queryset(users_qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=["GET"], detail=True, permission_classes=(GroupMemberPermission,))
    def get_invite_link(self, request, *args, **kwargs):
        """Endpoint to claim Group invitation link"""

        group = self.get_object()
        return Response({"invite_link": f"{request.get_host()}{reverse('group-invite')}?uuid={group.invitation_link}"})

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class InvitesView(
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = GroupInvitations.objects.all().prefetch_related("group")
    permission_classes = (IsAuthenticated, InviteePermission)
    serializer_class = GroupInvitationsSerializer

    def get_serializer_class(self):
        """Changing serializer class depends on actions"""

        if self.action == "list":
            return GroupInvitationsSerializer
        elif self.action == "create":
            return GroupInvitationsPostSerializer
        else:
            return super().get_serializer_class()

    @action(methods=["GET"], detail=False)
    def me(self, request, *args, **kwargs):
        """Endpoint for view current User's Group invites"""

        qs = GroupInvitations.objects.filter(invitee=request.user)

        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=["POST"], detail=True, serializer_class=serializers.Serializer)
    def accept(self, request, *args, **kwargs):
        """Endpoint for accepting pending Invites (for invitee)"""

        invite = self.get_object()
        gm = GroupMembers.objects.create(group=invite.group, member=invite.invitee)
        invite.delete()
        return Response({"accepted group": GroupSerializer(invite.group).data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=204)
