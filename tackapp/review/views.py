import logging

from rest_framework import viewsets, mixins
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from core.choices import TackStatus
from core.permissions import ReviewPermission
from review.models import Review
from review.serializers import ReviewSerializer


class ReviewViewset(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Review.active.all()
    serializer_class = ReviewSerializer
    permission_classes = (ReviewPermission,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # If User is not Tacker or Runner of the Tack - he is not allowed to create Review
        tack = serializer.validated_data["tack"]
        if not tack.is_participant(request.user):
            return Response({"detail": "You do not have permission to perform this action."}, status=400)
        # if tack.status != TackStatus.WAITING_REVIEW:
        #     return Response({"detail": f"Tack is not in status {TackStatus.WAITING_REVIEW}"}, status=400)

        try:
            review = Review.objects.get(tack=tack, user=request.user)
            return Response(
                {
                    "detail": "You are already have a review on this Tack",
                    "review": ReviewSerializer(review).data
                },
                status=400)
        except Review.DoesNotExist:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
        except MultipleObjectsReturned:
            logging.getLogger().error(f"Multiple reviews found, {serializer.data}")
            return Response({"detail": "Multiple reviews found"}, status=400)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
