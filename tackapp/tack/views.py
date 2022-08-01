import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import views, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import *
from core.choices import TackStatus, OfferType
from group.models import GroupTacks
from .serializers import *
from .services import accept_offer, complete_tack
from .tasks import change_tack_status_finished, delete_offer_task


class TackViewset(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tack.objects.all()
    serializer_class = TackDetailSerializer
    # TODO: ListView serializer for many tacks and Detailed serializer for single Tack
    permission_classes = (TackOwnerPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['status']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.active_group:
            return Response({"detail": "You need to set active group first"})
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        tack = self.get_object()
        serializer = self.get_serializer(tack, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if tack.status != TackStatus.created:
            return Response({"error": "You cannot change Tack with active offers"}, status=400)

        self.perform_update(serializer)

        if getattr(tack, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            tack._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        tack = self.get_object()
        if tack.status != TackStatus.created:
            return Response({"message": "You can not delete tacks while it have active offers"})
        self.perform_destroy(tack)
        return Response(status=204)

    @action(methods=["GET"], detail=False, url_path="me/as_tacker")
    def me_as_tacker(self, request, *args, **kwargs):
        """Endpoint to display current User's Tacks as Tacker"""

        qs = Tack.objects.filter(tacker=request.user).prefetch_related("tacker")
        qs = self.filter_queryset(qs)
        page = self.paginate_queryset(qs)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)

    # @action(methods=["GET"], detail=False, url_path="me/as_runner")
    # def me_as_runner(self, request, *args, **kwargs):
    #     """Endpoint to display current User's Tacks as Runner"""
    #
    #     qs = Tack.objects.filter(runner=request.user).prefetch_related("tacker")
    #     qs = self.filter_queryset(qs)
    #     page = self.paginate_queryset(qs)
    #     serializer = self.serializer_class(page, many=True)
    #     return self.get_paginated_response(serializer.data)

    @action(methods=["GET"], detail=False, serializer_class=TacksOffersSerializer, url_path="me/as_runner")
    def me_as_runner(self, request, *args, **kwargs):
        """Endpoint to display current Users's Offers and related Tacks based on Offer entities"""

        offers = Offer.objects.filter(runner=request.user).select_related("tack", "tack__tacker", "runner", "tack__group")
        # tack_offers = TacksOffers.objects.all()
        # print(f"{offers = }")
        # new_offers = [[offer, offer.tack] for offer in list(offers)]
        # print(new_offers)
        # for offer in offers:
        #     new_offers.append([offer, offer.tack])
        # print(new_offers)
        # tacks = Tack.objects.filter(offer__in=offers).prefetch_related("offer_set")
        # new_offers = offers | tacks
        page = self.paginate_queryset(offers)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=(TackFromRunnerPermission,),
        serializer_class=TackCompleteSerializer,
    )
    def complete(self, request, *args, **kwargs):
        """Endpoint for Runner to complete the Tack"""

        tack = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if tack.status != TackStatus.in_progress:
            return Response({"detail": "Current Tack status is not In Progress"})

        complete_tack(tack, serializer.validated_data["message"])
        task = change_tack_status_finished.apply_async(countdown=43200, kwargs={"tack_id": tack.id})
        return Response(serializer.data, status=200)

    @action(
        methods=["POST"],
        detail=True,
        serializer_class=serializers.Serializer,
        permission_classes=(TackFromRunnerPermission,)
    )
    def start_tack(self, request, *args, **kwargs):
        """Endpoint for Runner to start doing the Tack"""

        tack = self.get_object()
        tack.change_status(TackStatus.in_progress)
        return Response(self.get_serializer(tack).data)

    @action(methods=["GET"], detail=True, serializer_class=OfferSerializer, permission_classes=(StrictTackOwnerPermission,))
    def offers(self, request, *args, **kwargs):
        """Endpoint to display Offers related to specific Tack"""

        # TODO filter backend? maybe
        tack = self.get_object()
        offers = Offer.objects.filter(tack=tack)
        page = self.paginate_queryset(offers)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(tacker=self.request.user, group=self.request.user.active_group)
        # TODO: send notifications OR/AND make record in TackGroup table  (signals already?)

    def perform_update(self, serializer):
        serializer.save(tacker=self.request.user)


class OfferViewset(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = (OfferPermission,)  # TODO: Allows to see offers by id
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('offer_type',)

    def create(self, request, *args, **kwargs):
        """Endpoint for creating Runner-side offers. Provide price ONLY for Counter-offering"""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tack = serializer.validated_data["tack"]

        if serializer.validated_data.get("price") and (not tack.allow_counter_offer):
            return Response({"message": "Counter offering is not allowed to this Tack"}, status=403)
        if tack.tacker == request.user:
            return Response({"message": "You are not allowed to create Offers to your own Tacks"}, status=403)
        if Offer.objects.filter(tack=tack, runner=request.user):
            return Response({"message": "You already have an offer for this Tack"}, status=409)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=201, headers=headers)

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=(OfferTackOwnerPermission,),
        serializer_class=AcceptOfferSerializer
    )
    def accept(self, request, *args, **kwargs):
        """Endpoint for Tacker to accept Runner's offer"""

        # TODO: check Tacker balance
        # user.balance < tack.price - redirect on payment

        offer = self.get_object()
        price = offer.price if offer.price else offer.tack.price
        if request.user.bankaccount.usd_balance < price:
            return Response(
                {
                    "message": "Not enough money",
                    "balance": request.user.bankaccount.usd_balance,
                    "tack_price": price
                },
                status=400)

        accept_offer(offer)
        serializer = OfferSerializer(offer)
        return Response(serializer.data)

    @action(methods=["GET"], detail=False)
    def me(self, request, *args, **kwargs):
        qs = Offer.objects.filter(runner=request.user)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Endpoint for Runner to delete their own not accepted Offers"""

        instance = self.get_object()
        if instance.is_accepted:
            return Response({"message": "Cannot delete accepted Offers"})
        self.perform_destroy(instance)
        return Response(status=204)

    def perform_create(self, serializer):
        serializer.save(runner=self.request.user)
