from rest_framework import viewsets
from rest_framework.response import Response

from core.permissions import ReviewPermission
from review.models import Review
from review.serializers import ReviewSerializer


class ReviewViewset(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = (ReviewPermission,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # If User is not Tacker or Runner of the Tack - he is not allowed to create Review
        tack = serializer.validated_data["tack"]
        if not tack.is_participant(request.user):
            return Response({"detail": "You do not have permission to perform this action."})

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
