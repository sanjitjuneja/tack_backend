import datetime
import logging

from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import *
from tack.utils import set_pay_for_tack_id, stripe_desync_check
from .serializers import *
from .services import accept_offer, complete_tack, confirm_complete_tack, delete_tack_offers

logger = logging.getLogger('debug')


class TackViewset(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tack.active.all()
    serializer_class = TackDetailSerializer
    # TODO: ListView serializer for many tacks and Detailed serializer for single Tack
    permission_classes = (TackOwnerPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['status']

    def get_serializer_class(self):
        """Changing serializer class depends on actions"""

        if self.action == "partial_update" or self.action == "update":
            return TackCreateSerializer
        else:
            return super().get_serializer_class()

    @extend_schema(request=inline_serializer(
        name="tack_create_serializer_v2",
        fields={
            "tack": TackCreateSerializer(),
            "payment_info": PaymentInfoSerializer(),
        }
    ), responses=TackDetailSerializer)
    def create(self, request, *args, **kwargs):
        serializer = TackCreateSerializerv2(data=request.data)
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
        tack_info = serializer.validated_data.get("tack")
        payment_info = serializer.validated_data.get("payment_info") or {}
        transaction_id = payment_info.get("transaction_id", None)
        method_type = payment_info.get("method_type", None)

        try:
            GroupMembers.objects.get(member=request.user, group=tack_info["group"])
        except GroupMembers.DoesNotExist:
            return Response(
                {
                    "error": "Gx1",
                    "message": "You are not a member of this Group"
                },
                status=400)
        price = tack_info.get("price")
        with transaction.atomic():
            if tack_info.get("auto_accept"):
                match method_type:
                    case MethodType.TACK_BALANCE:
                        pass
                    case MethodType.STRIPE:
                        if request.user.bankaccount.usd_balance < price and transaction_id:
                            stripe_desync_check(request, transaction_id)
                    case MethodType.DWOLLA:
                        pass
                    case _:
                        pass

                ba = BankAccount.objects.get(user=request.user)
                if ba.usd_balance < price:
                    return Response(
                        {
                            "error": "Px2",
                            "message": "Not enough money",
                            "balance": ba.usd_balance,
                            "tack_price": price
                        },
                        status=400)
                ba.usd_balance -= price
                ba.usd_balance.save()
            tack = self.perform_create(serializer)
        if transaction_id:
            set_pay_for_tack_id(transaction_id, tack)
        output_serializer = TackDetailSerializer(tack, context={"request": request})
        return Response(output_serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        tack = self.get_object()
        serializer = self.get_serializer(tack, data=request.data, partial=partial)
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

        logger.debug(f"{serializer.validated_data = }")

        if tack.status != TackStatus.CREATED:
            return Response(
                {
                    "error": "Tx1",
                    "message": "You cannot change Tack with active offers"
                },
                status=400)

        self.perform_update(serializer)

        if getattr(tack, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            tack._prefetched_objects_cache = {}

        return Response(TackDetailSerializer(tack, context={"request": request}).data)

    def destroy(self, request, *args, **kwargs):
        tack = self.get_object()
        if tack.status not in (TackStatus.CREATED, TackStatus.ACTIVE):
            return Response(
                {
                    "error": "Tx2",
                    "message": "You can not delete tacks when you accepted an Offer"
                },
                status=400)
        with transaction.atomic():
            delete_tack_offers(tack)
            if tack.auto_accept:
                request.user.bankaccount.usd_balance += tack.price
                request.user.bankaccount.save()
            self.perform_destroy(tack)
        return Response(status=204)

    @action(methods=["GET"], detail=False, url_path="me/as_tacker")
    def me_as_tacker(self, request, *args, **kwargs):
        """Endpoint to display current User's Tacks as Tacker"""

        tacks = Tack.active.filter(
            tacker=request.user
        ).exclude(
            status=TackStatus.FINISHED
        ).order_by(
            "-creation_time"
        ).prefetch_related(
            "tacker",
            "runner",
            "group"
        )
        tacks = self.filter_queryset(tacks)
        serializer = self.serializer_class(tacks, many=True, context={"request": request})
        return Response(serializer.data)

    @action(methods=["GET"], detail=False, serializer_class=TacksOffersSerializer, url_path="me/as_runner")
    def me_as_runner(self, request, *args, **kwargs):
        """Endpoint to display current Users's Offers and related Tacks based on Offer entities"""

        offers = Offer.objects.filter(
            status__in=(
                OfferStatus.ACCEPTED,
                OfferStatus.CREATED,
                OfferStatus.IN_PROGRESS,
                OfferStatus.FINISHED
            ),
            runner=request.user
        ).exclude(
            tack__status=TackStatus.FINISHED
        ).order_by(
            "-creation_time"
        ).select_related(
            "tack",
            "tack__tacker",
            "runner",
            "tack__group"
        )
        serializer = self.get_serializer(offers, many=True, context={"request": request})
        return Response(serializer.data)

    @action(methods=("GET",), detail=False, url_path="me/previous_as_tacker")
    def previous_as_tacker(self, request, *args, **kwargs):
        queryset = Tack.active.filter(
            tacker=request.user,
            status=TackStatus.FINISHED
        ).order_by(
            "-creation_time"
        ).prefetch_related(
            "tacker",
            "runner",
            "group"
        )
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @action(methods=("GET",), detail=False, url_path="me/previous_as_runner")
    def previous_as_runner(self, request, *args, **kwargs):
        """Endpoint to display current Users's Offers and related Tacks based on Offer entities"""

        offers = Tack.active.filter(
            runner=request.user,
            status=TackStatus.FINISHED
        ).order_by(
            "-creation_time"
        ).select_related(
            "tacker",
            "runner",
            "group"
        )
        page = self.paginate_queryset(offers)
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @extend_schema(request=None)
    @action(
        methods=("POST",),
        detail=True,
        permission_classes=(TackFromRunnerPermission,),
    )
    def complete(self, request, *args, **kwargs):
        """Endpoint for Runner to complete the Tack"""

        tack = self.get_object()
        if tack.status != TackStatus.IN_PROGRESS:
            return Response(
                {
                    "error": "Tx3",
                    "message": "Current Tack status is not In Progress"
                },
                status=400)

        complete_tack(tack)
        return Response(status=200)

    @extend_schema(request=None, responses={
        200: inline_serializer(
            name="Test",
            fields={
                "error": serializers.CharField(allow_null=True),
                "is_ongoing_runner_tack": serializers.BooleanField()
            }
        )})
    @action(
        methods=("GET",),
        detail=False,
        url_path="me/ongoing-runner-tacks"
    )
    def ongoing_runner_tacks(self, request, *args, **kwargs):
        ongoing_runner_tacks = Tack.active.filter(
            runner=request.user,
            status=TackStatus.IN_PROGRESS
        )
        return Response(
            {
                "error": None,
                "message": None,
                "is_ongoing_runner_tack": ongoing_runner_tacks.exists()
            },
            status=200)

    @extend_schema(request=None)
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=(TackFromRunnerPermission,)
    )
    def start_tack(self, request, *args, **kwargs):
        """Endpoint for Runner to start doing the Tack"""

        tack = self.get_object()
        ongoing_runner_tacks = Tack.active.filter(
            runner=request.user,
            status=TackStatus.IN_PROGRESS
        )
        if ongoing_runner_tacks.exists():
            return Response(
                {
                    "error": "Tx4",
                    "message": "You already have ongoing Tack"
                },
                status=400)
        with transaction.atomic():
            tack.status = TackStatus.IN_PROGRESS
            tack.accepted_offer.status = OfferStatus.IN_PROGRESS
            tack.start_completion_time = timezone.now()
            tack.save()
            tack.accepted_offer.save()
        return Response(self.get_serializer(tack).data)

    @action(methods=["GET"], detail=True, serializer_class=OfferSerializer,
            permission_classes=(StrictTackOwnerPermission,))
    def offers(self, request, *args, **kwargs):
        """Endpoint to display Offers related to specific Tack"""

        tack = self.get_object()
        offers = Offer.active.filter(tack=tack).prefetch_related("runner")
        page = self.paginate_queryset(offers)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @extend_schema(request=None)
    @action(methods=["GET"], detail=False)
    def nearby(self, request, *args, **kwargs):
        """Endpoint for getting manual Popular templates"""

        popular_tacks = PopularTack.objects.filter(group__isnull=True)[:10]
        serializer_popular = PopularTackSerializer(popular_tacks, many=True)
        return Response({
            "popular": serializer_popular.data,
        })

    @extend_schema(request=None)
    @action(methods=("POST",), detail=True, permission_classes=(TackOwnerPermission,))
    def confirm_complete(self, request, *args, **kwargs):
        """Endpoint for Tacker to send payment to Runner without creating Review"""

        tack = self.get_object()
        if tack.status == TackStatus.WAITING_REVIEW:
            confirm_complete_tack(tack)
            return Response(TackDetailSerializer(tack).data)
        else:
            return Response(
                {
                    "error": "Tx5",
                    "message": "Tack status is not in status Waiting Review"
                },
                status=400)

    @action(
        methods=("GET",),
        detail=True,
        permission_classes=(TackParticipantPermission,),
        serializer_class=ContactsSerializer
    )
    def get_contacts(self, request, *args, **kwargs):
        tack = self.get_object()
        if tack.status in (TackStatus.CREATED, TackStatus.ACTIVE):
            return Response(
                {
                    "error": "Tx6",
                    "message": "You cannot get contact data for Unaccepted Offer"
                },
                status=400)
        contacts = tack.runner.get_contacts() if tack.tacker == request.user else tack.tacker.get_contacts()
        logger.debug(contacts)
        serializer = ContactsSerializer(contacts)
        return Response(serializer.data)

    @extend_schema(request=None)
    @action(methods=("POST",), detail=True, permission_classes=(TackFromRunnerPermission,))
    def runner_cancel(self, request, *args, **kwargs):
        tack = self.get_object()
        if tack.status not in (TackStatus.ACCEPTED, TackStatus.IN_PROGRESS):
            return Response(
                {
                    "error": "Tx7",
                    "message": "Cannot cancel Tack in this status"
                },
                status=400)
        tack.cancel()
        serializer = self.get_serializer(tack)
        return Response(serializer.data)

    def perform_create(self, serializer):
        return serializer.save(tacker=self.request.user)

    def perform_update(self, serializer):
        serializer.save(tacker=self.request.user)


class OfferViewset(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Offer.active.all()
    serializer_class = OfferSerializer
    permission_classes = (OfferPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('offer_type',)

    def create(self, request, *args, **kwargs):
        """Endpoint for creating Runner-side offers. Provide price ONLY for Counter-offering"""

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
        tack = serializer.validated_data["tack"]

        if serializer.validated_data.get("price") and (not tack.allow_counter_offer):
            return Response(
                {
                    "error": "Tx8",
                    "message": "Counter offering is not allowed to this Tack"
                },
                status=400)
        if tack.tacker == request.user:
            return Response(
                {
                    "error": "Tx9",
                    "message": "You are not allowed to create Offers to your own Tacks"
                },
                status=400)
        if Offer.active.filter(tack=tack, runner=request.user):
            return Response(
                {
                    "error": "Tx10",
                    "message": "You already have an offer for this Tack"
                },
                status=400)
        if tack.status not in (TackStatus.ACTIVE, TackStatus.CREATED):
            return Response(
                {
                    "error": "Tx11",
                    "message": "You can create Offers only on Active Tacks"
                },
                status=400)
        created_offer = self.perform_create(serializer)
        if tack.auto_accept:
            accept_offer(created_offer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=201, headers=headers)

    @action(
        methods=("POST",),
        detail=True,
        permission_classes=(OfferTackOwnerPermission,),
        serializer_class=AcceptOfferSerializer
    )
    def accept(self, request, *args, **kwargs):
        """Endpoint for Tacker to accept Runner's offer"""

        offer = self.get_object()
        if offer.status != OfferStatus.CREATED:
            return Response(
                {
                    "error": "Tx13",
                    "message": "Offer already accepted"
                },
                status=400
            )
        data = request.data if request.data else {}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        # TODO: to service
        price = offer.price if offer.price else offer.tack.price
        logger.info(f"{request.user.bankaccount.usd_balance = }")
        payment_info = serializer.validated_data.get("payment_info") or {}
        transaction_id = payment_info.get("transaction_id", None)
        method_type = payment_info.get("method_type", None)

        logger.debug(f"Tack id {offer.tack_id} paid by {method_type}")
        match method_type:
            case MethodType.TACK_BALANCE:
                pass
            case MethodType.STRIPE:
                set_pay_for_tack_id(transaction_id, offer.tack)
                if request.user.bankaccount.usd_balance < price and transaction_id:
                    stripe_desync_check(request, transaction_id)
            case MethodType.DWOLLA:
                set_pay_for_tack_id(transaction_id, offer.tack)
            case _:
                pass

        ba = BankAccount.objects.get(user=request.user)
        logger.debug(f"{ba = }")
        if ba.usd_balance < price:
            return Response(
                {
                    "error": "Px2",
                    "message": "Not enough money",
                    "balance": ba.usd_balance,
                    "tack_price": price
                },
                status=400)

        accept_offer(offer)
        serializer = OfferSerializer(offer)
        return Response(serializer.data)

    @action(methods=["GET"], detail=False)
    def me(self, request, *args, **kwargs):
        """Endpoint for getting owned Offers"""

        qs = Offer.active.filter(
            runner=request.user
        ).order_by(
            "-creation_time"
        )
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Endpoint for Runner to delete their own not accepted Offers"""

        instance = self.get_object()
        if instance.status == OfferStatus.ACCEPTED:
            return Response(
                {
                    "error": "Tx12",
                    "message": "Cannot delete accepted Offers"
                },
                status=400)
        self.perform_destroy(instance)
        return Response(status=204)

    def perform_create(self, serializer):
        return serializer.save(runner=self.request.user)
