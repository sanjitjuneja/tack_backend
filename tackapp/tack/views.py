from rest_framework import viewsets, mixins
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import *
from .serializers import *


class TackViewset(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tack.objects.all()
    serializer_class = TackDetailSerializer
    # TODO: ListView serializer for many tacks and Detailed serializer for single Tack
    permission_classes = (TackOwnerPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['status']

    def perform_create(self, serializer):
        serializer.save(tacker=self.request.user)
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
    permission_classes = (OfferPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('offer_type',)
