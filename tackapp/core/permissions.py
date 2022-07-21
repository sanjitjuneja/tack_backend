from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission, SAFE_METHODS


class TackOwnerPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.tacker == request.user


class TackFromRunnerPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.runner == request.user


class StrictTackOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.tacker == request.user


class OfferPermission(BasePermission):
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


class InviterOrInviteePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.inviter == request.user or obj.invitee == request.user