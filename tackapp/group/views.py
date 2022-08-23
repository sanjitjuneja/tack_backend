import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, parsers, mixins
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.choices import TackStatus
from core.permissions import GroupOwnerPermission, GroupMemberPermission, InviteePermission
from tack.models import Tack, PopularTack, Offer
from tack.serializers import TackDetailSerializer, PopularTackSerializer, TackTemplateSerializer
from .serializers import *
from .services import get_tacks_by_group


class GroupViewset(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Group.active.all()
    serializer_class = GroupSerializer
    permission_classes = (GroupOwnerPermission,)
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)

    @action(methods=["GET"], detail=False)
    def me(self, request, *args, **kwargs):
        """Endpoint for get all User's groups he is member of"""

        qs = Group.active.filter(groupmembers__member=request.user)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

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
            GroupMembers.objects.get(group=group, member=request.user)
        except Group.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        except GroupMembers.DoesNotExist:
            invite, created = GroupInvitations.objects.get_or_create(invitee=request.user, group=group)
            invite_serializer = GroupInvitationsSerializer(invite)
            return Response({"invitation": invite_serializer.data})
        return Response({"group": GroupSerializer(group).data})

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
        tacks = Tack.active.filter(
            group=group,
            status__in=[TackStatus.CREATED, TackStatus.ACTIVE],
        ).exclude(
            offer__runner=request.user
        ).select_related("tacker", "runner", "group")
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
        protocol = 'https' if request.is_secure() else 'http'
        return Response({"invite_link": f"{protocol}://{request.get_host()}{reverse('group-invite')}?uuid={group.invitation_link}"})

    @action(methods=["GET"], detail=True, permission_classes=(GroupMemberPermission,), url_path="me/tacks")
    def my_tacks(self, request, *args, **kwargs):
        """Endpoint for getting all current User's Tacks"""

        group = self.get_object()
        tacks = Tack.active.filter(
            group=group,
            status__in=[TackStatus.CREATED, TackStatus.ACTIVE],
            tacker=request.user
        ).select_related("tacker", "runner", "group")
        page = self.paginate_queryset(tacks)
        serializer = TackDetailSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=["POST"], detail=True, permission_classes=(GroupMemberPermission,), serializer_class=serializers.Serializer)
    def mute(self, request, *args, **kwargs):
        group = self.get_object()
        GroupMutes.objects.get_or_create(user=request.user, group=group)
        return Response(GroupSerializer(group).data)

    @action(methods=["POST"], detail=True, permission_classes=(GroupMemberPermission,), serializer_class=serializers.Serializer)
    def unmute(self, request, *args, **kwargs):
        group = self.get_object()
        try:
            mute = GroupMutes.objects.get(user=request.user, group=group)
            mute.delete()
        except ObjectDoesNotExist:
            pass

        return Response(GroupSerializer(group).data)

    @action(methods=["GET"], detail=True, permission_classes=(GroupMemberPermission,), serializer_class=serializers.Serializer)
    def popular_tacks(self, request, *args, **kwargs):
        group = self.get_object()
        popular_tacks = PopularTack.objects.filter(group=group)[:10]
        tacks_len = 10 - len(popular_tacks)
        tacks = Tack.active.filter(
            group=group,
            status__in=[TackStatus.WAITING_REVIEW, TackStatus.FINISHED]
        ).annotate(
            offer_count=Count('offer')
        ).order_by(
            "-offer_count"
        )[:tacks_len]
        # logging.getLogger().warning(tacks.query)

        serializer_popular = PopularTackSerializer(popular_tacks, many=True)
        serializer_default = TackTemplateSerializer(tacks, many=True)
        return Response({
            "popular": serializer_popular.data,
            "groups": serializer_default.data
        })

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
        GroupMembers.objects.create(group=invite.group, member=invite.invitee)
        invite.delete()
        return Response({"accepted group": GroupSerializer(invite.group).data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=204)
