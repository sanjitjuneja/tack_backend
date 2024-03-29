from rest_framework import viewsets, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

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

        # If User is not Tacker or Runner of the Tack - he is not allowed to create Review
        tack = serializer.validated_data["tack"]
        if not tack.is_participant(request.user):
            return Response(
                {
                    "error": "Rx1",
                    "message": "You do not have permission to perform this action."
                },
                status=400)

        try:
            review = Review.objects.get(tack=tack, user=request.user)
            return Response(
                {
                    "error": "Rx2",
                    "message": "You are already have a review on this Tack",
                    "review": ReviewSerializer(review).data
                },
                status=400)
        except Review.DoesNotExist:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
