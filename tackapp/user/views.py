import logging

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from rest_framework import filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.choices import TackStatus
from payment.models import BankAccount
from payment.serializers import BankAccountSerializer
from review.serializers import ReviewSerializer
from stats.models import UserVisits
from tack.models import Tack
from .documents import UserDocument
from elasticsearch_dsl import Q as ESQ
from .serializers import *
from .services import get_reviews_by_user, get_reviews_as_reviewer_by_user, user_change_bio

logger = logging.getLogger('debug')


class UsersViewset(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', '=phone_number', 'first_name', 'last_name')

    def get_serializer_class(self):
        """Changing serializer class depends on actions"""

        if self.action == "partial_update" or self.action == "update":
            return UserDetailSerializer
        else:
            return super().get_serializer_class()

    @action(methods=("GET",), detail=False, serializer_class=UserDetailSerializer)
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=("PATCH",),
        detail=False,
        url_path="me/change_bio",
        serializer_class=UserDetailSerializer
    )
    def me_change_bio(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
        user = user_change_bio(request.user, serializer.validated_data)

        return Response(self.get_serializer(user).data)

    @extend_schema(request=None, responses={
        204: inline_serializer(
            name="Deleted_successfully",
            fields={
                "error": serializers.CharField(allow_null=True),
                "message": serializers.CharField(allow_null=True),
            }
        ),
        400: inline_serializer(
            name="Error",
            fields={
                "error": serializers.CharField(allow_null=True),
                "message": serializers.CharField(allow_null=True),
            }
        )})
    @action(methods=("POST",), detail=False, url_path="me/delete_account")
    def me_delete(self, request, *args, **kwargs):
        active_tacks = Tack.active.filter(
            Q(tacker=request.user) | Q(runner=request.user),
            status__in=(
                TackStatus.ACCEPTED,
                TackStatus.IN_PROGRESS,
                TackStatus.WAITING_REVIEW
            )
        )
        if active_tacks:
            return Response(
                {
                    "error": "Ux5",
                    "message": "Cannot delete User. You have active Tacks"
                },
                status=400)
        ba = BankAccount.objects.get(user=request.user)
        if ba.usd_balance > 0:
            return Response(
                {
                    "error": "Ux6",
                    "message": "User balance is not 0"
                },
                status=400)

        # deactivate_dwolla_customer(request.user)
        request.user.delete()  # delete_stripe_dwolla_account signal will do the job
        return Response(
            {
                "error": None,
                "message": "Successfully deleted"
            },
            status=204)

    @action(methods=("GET",), detail=True)
    def reviews_as_reviewed(self, request, *args, **kwargs):
        """Endpoint for get all Reviews of the User as reviewed"""

        user = self.get_object()
        reviews_qs = get_reviews_by_user(user)
        page = self.paginate_queryset(reviews_qs)
        serializer = ReviewSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=("GET",), detail=True)
    def reviews_as_reviewer(self, request, *args, **kwargs):
        """Endpoint for get all Reviews of the User as reviewer"""

        user = self.get_object()
        reviews_qs = get_reviews_as_reviewer_by_user(user)
        page = self.paginate_queryset(reviews_qs)
        serializer = ReviewSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(methods=("GET",), detail=False, url_path="me/balance", serializer_class=BankAccountSerializer)
    def balance(self, request, *args, **kwargs):
        """Endpoint for retrieving USD balance of current User"""

        ba, created = BankAccount.objects.get_or_create(user=request.user)
        return Response(BankAccountSerializer(ba).data)

    @action(methods=("POST",), detail=False, url_path="me/visit", serializer_class=None)
    def add_visit(self, request, *args, **kwargs):
        logger.info(f"{request.data = }")
        logger.info(f"{request.META = }")
        UserVisits.objects.create(
            user=request.user
        )
        return Response()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='query',
                location=OpenApiParameter.QUERY,
                description='Search Query string',
                required=True,
                type=OpenApiTypes.STR
            ),
        ],
    )
    @action(methods=("GET",), detail=False, serializer_class=None)
    def search(self, request, *args, **kwargs):
        logger.debug(f"{kwargs = }")
        query = request.GET['query']
        search = UserDocument.search().query(
            ESQ(
                'multi_match',
                query=query + '*',
                fields=(
                    'first_name^3',
                    'last_name^5'
                ),
            ),
        )
        response = search.execute()
        for hit in response.hits:
            logger.debug(f"{hit = }")
        # logger.debug(f'ES {response.hits = }')
        return Response({"response": str(response)})
