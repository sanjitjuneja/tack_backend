import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import viewsets, parsers, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.choices import TackStatus, OfferStatus
from core.permissions import GroupOwnerPermission, GroupMemberPermission, InviteePermission
from tack.models import Tack, PopularTack, Offer
from tack.serializers import TackDetailSerializer, PopularTackSerializer, GroupTackSerializer
from user.serializers import UserListSerializer
from .serializers import *


logger = logging.getLogger("django")


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

    def get_permissions(self):
        if self.action == "retrieve":  # per action
            self.permission_classes = (GroupMemberPermission,)
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        group = self.get_object()
        try:
            gm = GroupMembers.objects.get(group=group, member=request.user)
        except GroupMembers.DoesNotExist:
            return Response(
                {
                    "error": "Gx1",
                    "message": "You are not a member of this Group"
                },
                status=400
            )

        serializer = GroupMembersSerializer(gm, context={"request": request})
        return Response(serializer.data)

    @action(methods=("GET",), detail=False, serializer_class=GroupMembersSerializer)
    def me(self, request, *args, **kwargs):
        """Endpoint for get all User's groups he is member of"""

        qs = GroupMembers.objects.filter(
            member=request.user
        ).order_by(
            "-date_joined"
        ).select_related(
            "group"
        )
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @extend_schema(request=None)
    @action(
        methods=("POST",),
        detail=True,
        permission_classes=(GroupMemberPermission,)
    )
    def set_active(self, request, *args, **kwargs):
        """Endpoint for setting active Group to the User (for further Tack creation)"""

        group = self.get_object()
        if not request.user.active_group == group:
            request.user.active_group = group
            request.user.save()
        serializer = GroupSerializer(group, context={"request": request})
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
        methods=("GET",),
        detail=False,
        serializer_class=GroupInviteLinkSerializer,
        permission_classes=(AllowAny,)
    )
    def invite(self, request, *args, **kwargs):
        """Endpoint for accepting invitation from Invitation Link"""

        if request.user.is_anonymous:
            logger.info(f"{request.META = }")
            return redirect("https://apps.apple.com/us/app/tack-task-marketplace/id1619995138")

        serializer = self.get_serializer(data=request.query_params)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                {
                    "error": "Ox3",
                    "message": "Validation error. Some of the fields have invalid values",
                    "details": e.detail,
                },
                status=400)
        uuid = serializer.validated_data["uuid"]
        try:
            group = self.get_queryset().get(invitation_link=uuid)
            gm = GroupMembers.objects.get(group=group, member=request.user)
        except Group.DoesNotExist:
            return Response({"error": "code", "message": "Group not found"}, status=404)
        except GroupMembers.DoesNotExist:
            invite, created = GroupInvitations.objects.get_or_create(invitee=request.user, group=group)
            invite_serializer = GroupInvitationsSerializer(invite, context={"request": request})
            return Response({"invitation": invite_serializer.data})
        return Response({"group": GroupMembersSerializer(gm, context={"request": request}).data})

    @extend_schema(
        responses={
            200: inline_serializer(
                name="leave_200",
                fields={
                    "message": serializers.CharField(),
                    "group": GroupSerializer()
                }
            ),
            400: inline_serializer(
                name="leave_400",
                fields={
                    "error": serializers.CharField(),
                    "message": serializers.CharField()
                }
            )
        }
    )
    @action(methods=("POST",), detail=True, permission_classes=(GroupMemberPermission,),
            serializer_class=serializers.Serializer)
    def leave(self, request, *args, **kwargs):
        """Endpoint for leaving Group"""

        group = self.get_object()
        try:
            gm = GroupMembers.objects.get(member=request.user, group=group)

            ongoing_tacks = Tack.active.filter(
                Q(tacker=request.user) | Q(runner=request.user),
                status__in=(
                    TackStatus.CREATED,
                    TackStatus.ACTIVE,
                    TackStatus.ACCEPTED,
                    TackStatus.IN_PROGRESS,
                    TackStatus.WAITING_REVIEW
                ),
                group=group
            )
            logging.getLogger().warning(f"{ongoing_tacks = }")

            # check if User have ongoing Tacks right now
            if ongoing_tacks.exists():
                return Response(
                    {
                        "error": "Gx2",
                        "message": "You can't leave this group. You have ongoing Tacks"
                    },
                    status=400)

            # if request.user.active_group == group:
            #     request.user.active_group = None
            #     request.user.save()
            gm.delete()
            group.member_count -= 1
            group.save()
        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "Gx1",
                    "message": "You are not a member of this group"},
                status=400)
        return Response(
            {
                "error": None,
                "message": "Leaved Successfully",
                "group": GroupSerializer(group, context={"request": request}).data
            },
            status=200)

    @action(
        methods=("GET",),
        detail=True,
        serializer_class=GroupTackSerializer,
        permission_classes=(GroupMemberPermission,)
    )
    def tacks(self, request, *args, **kwargs):
        """Endpoint for getting *created* and *active* Tacks of certain Group"""

        group = self.get_object()
        tacks = Tack.active.filter(
            group=group,
            status__in=(TackStatus.CREATED, TackStatus.ACTIVE),
        ).prefetch_related(
            Prefetch("offer_set", queryset=Offer.active.filter(runner=request.user))
        ).select_related(
            "tacker",
            "runner",
            "group",
        ).order_by(
            "-creation_time"
        )
        page = self.paginate_queryset(tacks)
        serializer = GroupTackSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @action(
        methods=("GET",),
        detail=True,
        serializer_class=UserListSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def members(self, request, *args, **kwargs):
        group = self.get_object()
        users_qs = User.objects.filter(groupmembers__group=group)
        page = self.paginate_queryset(users_qs)
        serializer = self.get_serializer(page, many=True, context={"request", request})
        return self.get_paginated_response(serializer.data)

    @action(methods=("GET",), detail=True, permission_classes=(GroupMemberPermission,))
    def get_invite_link(self, request, *args, **kwargs):
        """Endpoint to claim Group invitation link"""

        group = self.get_object()
        protocol = 'https' if request.is_secure() else 'http'
        return Response(
            {
                "error": None,
                "message": None,
                "invite_link": (f"{protocol}://"
                                f"{request.get_host()}"
                                f"{reverse('group-invite')}"
                                f"?uuid={group.invitation_link}")
            }
        )

    @action(
        methods=("GET",),
        detail=True,
        permission_classes=(GroupMemberPermission,),
        url_path="me/tacks"
    )
    def my_tacks(self, request, *args, **kwargs):
        """Endpoint for getting all current User's Tacks"""

        group = self.get_object()
        tacks = Tack.active.filter(
            group=group,
            status__in=(TackStatus.CREATED, TackStatus.ACTIVE),
            tacker=request.user
        ).select_related(
            "tacker",
            "runner",
            "group"
        )
        page = self.paginate_queryset(tacks)
        serializer = TackDetailSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @action(
        methods=("GET",),
        detail=False,
        serializer_class=GroupSerializer,
        permission_classes=(AllowAny,)
    )
    def get_all_public(self, request, *args, **kwargs):
        """Endpoint for getting list of all public groups"""

        qs = Group.objects.filter(
            is_public=True
        ).order_by(
            "-member_count"
        )
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @extend_schema(request=None)
    @action(
        methods=("POST",),
        detail=True,
        permission_classes=(GroupMemberPermission,),
    )
    def mute(self, request, *args, **kwargs):
        group = self.get_object()
        try:
            gm = GroupMembers.objects.get(member=request.user, group=group)
            gm.is_muted = True
            gm.save()
        except GroupMembers.DoesNotExist:
            return Response(
                {
                    "error": "Gx1",
                    "message": "You are not a member of this group"
                },
                status=400)
        return Response(GroupMembersSerializer(gm, context={"request": request}).data)

    @extend_schema(request=None)
    @action(
        methods=("POST",),
        detail=True,
        permission_classes=(GroupMemberPermission,),
    )
    def unmute(self, request, *args, **kwargs):
        group = self.get_object()
        try:
            gm = GroupMembers.objects.get(member=request.user, group=group)
            gm.is_muted = False
            gm.save()
        except GroupMembers.DoesNotExist:
            return Response(
                {
                    "error": "Gx1",
                    "message": "You are not a member of this group"
                },
                status=400)

        return Response(GroupMembersSerializer(gm, context={"request": request}).data)

    @extend_schema(request=None)
    @action(
        methods=("GET",),
        detail=True,
        permission_classes=(GroupMemberPermission,),
    )
    def popular_tacks(self, request, *args, **kwargs):
        group = self.get_object()
        popular_tacks = PopularTack.objects.filter(group=group)[:10]
        tacks_len = 10 - len(popular_tacks)
        tacks = Tack.active.filter(
            group=group,
            status__in=(TackStatus.WAITING_REVIEW, TackStatus.FINISHED)
        ).annotate(
            offer_count=Count('offer', filter=~Q(offer__status=OfferStatus.DELETED))
        ).order_by(
            "-offer_count"
        )[:tacks_len]
        serializer_popular = PopularTackSerializer(popular_tacks, many=True)
        serializer_default = PopularTackSerializer(tacks, many=True)
        return Response(
            {
                "popular": serializer_popular.data + serializer_default.data,
            }
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class InvitesView(
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = GroupInvitations.objects.all().select_related("group")
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

    @action(methods=("GET",), detail=False)
    def me(self, request, *args, **kwargs):
        """Endpoint for view current User's Group invites"""

        qs = GroupInvitations.objects.filter(invitee=request.user).select_related("group")
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @extend_schema(request=None)
    @action(methods=("POST",), detail=True)
    def accept(self, request, *args, **kwargs):
        """Endpoint for accepting pending Invites (for invitee)"""

        invite = self.get_object()
        with transaction.atomic():
            GroupMembers.objects.create(group=invite.group, member=invite.invitee)
            group = Group.objects.get(group=invite.group)
            group.member_count += 1
            group.save()
            invite.delete()
        return Response(
            {
                "accepted group": GroupSerializer(
                    invite.group,
                    context={
                        "request": request
                    }
                ).data
            }
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=204)
