from rest_framework import filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from review.serializers import ReviewSerializer
from .serializers import *
from .services import get_reviews_by_user, get_reviews_as_reviewer_by_user, user_change_bio


class UsersViewset(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', '=phone_number')

    def get_serializer_class(self):
        """Changing serializer class depends on actions"""

        if self.action == "partial_update" or self.action == "update":
            return UserDetailSerializer
        else:
            return super().get_serializer_class()

    @action(methods=["GET"], detail=False, serializer_class=UserDetailSerializer)
    def me(self, request, *args, **kwargs):
        self.queryset = User.objects.all().prefetch_related("bankaccount")
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(methods=["PATCH"], detail=False, url_path="me/change_bio", serializer_class=UserDetailSerializer)
    def me_change_bio(self, request, *args, **kwargs):
        self.queryset = User.objects.all().prefetch_related("bankaccount")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = user_change_bio(request.user, serializer.validated_data)

        return Response(self.get_serializer(user).data)

    @action(methods=["GET"], detail=True)
    def reviews_as_reviewed(self, request, *args, **kwargs):
        """Endpoint for get all Reviews of the User as reviewed"""

        user = self.get_object()
        reviews_qs = get_reviews_by_user(user)
        page = self.paginate_queryset(reviews_qs)
        serializer = ReviewSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=["GET"], detail=True)
    def reviews_as_reviewer(self, request, *args, **kwargs):
        """Endpoint for get all Reviews of the User as reviewer"""

        user = self.get_object()
        reviews_qs = get_reviews_as_reviewer_by_user(user)
        page = self.paginate_queryset(reviews_qs)
        serializer = ReviewSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
