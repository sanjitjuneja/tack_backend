from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission, SAFE_METHODS

from group.models import GroupMembers


class TackOwnerPermission(BasePermission):
    """Permission for checking if User is owner of a Tack"""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.tacker == request.user


class TackFromRunnerPermission(BasePermission):
    """Permission for checking if User is Runner of a Tack"""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.runner == request.user


class StrictTackOwnerPermission(BasePermission):
    # TODO: deprecated to TackOwnerPermission?
    """Permission for checking if User is owner of a Tack"""

    def has_object_permission(self, request, view, obj):
        return obj.tacker == request.user


class OfferPermission(BasePermission):
    """Permission for checking if User is Runner of Offer"""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.runner == request.user


class OfferTackOwnerPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.tack.tacker == request.user


class GroupOwnerPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class InviteePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.invitee == request.user


class GroupMemberPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        try:
            GroupMembers.objects.get(group=obj, member=request.user)
        except ObjectDoesNotExist:
            return False

        return True


class ReviewPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
