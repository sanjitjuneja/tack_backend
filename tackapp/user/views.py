from rest_framework import filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from review.serializers import ReviewSerializer
from .serializers import *
from .services import get_reviews_by_user, get_reviews_as_reviewer_by_user


class UsersViewset(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', '=phone_number')

    @action(methods=["GET"], detail=True)
    def reviews_as_reviewed(self, request, *args, **kwargs):
        """Endpoint for get all Reviews of the User as reviewed"""

        user = self.get_object()
        reviews_qs = get_reviews_by_user(user)
        serializer = ReviewSerializer(reviews_qs, many=True)
        return Response(serializer.data)

    @action(methods=["GET"], detail=True)
    def reviews_as_reviewer(self, request, *args, **kwargs):
        """Endpoint for get all Reviews of the User as reviewer"""

        user = self.get_object()
        reviews_qs = get_reviews_as_reviewer_by_user(user)
        serializer = ReviewSerializer(reviews_qs, many=True)
        return Response(serializer.data)
