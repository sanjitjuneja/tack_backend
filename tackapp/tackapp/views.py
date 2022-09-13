import logging

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from fcm_django.models import FCMDevice
from rest_framework import views
from rest_framework.response import Response

from tackapp.serializers import NotificationSerializer
from firebase_admin.messaging import Message, Notification

logger = logging.getLogger()


class HealthCheck(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response()


class NotificationView(views.APIView):
    @extend_schema(request=NotificationSerializer, responses=NotificationSerializer)
    def post(self, request, *args, **kwargs):
        message = Message(
            notification=Notification(title="title", body="First one", image="url"),
            data={
                "Nick": "Mario",
                "body": "great match!",
                "Room": "PortugalVSDenmark"
            },
        )
        serializer = NotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        devices = FCMDevice.objects.filter(user_id=serializer.validated_data["user"])
        logger.warning(f"{devices = }")
        response = devices.send_message(message)
        logger.warning(f"{response = }")
        return Response()
