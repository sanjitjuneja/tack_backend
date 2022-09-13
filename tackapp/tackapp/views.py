import logging
import datetime

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from fcm_django.models import FCMDevice
from firebase_admin import messaging
from rest_framework import views
from rest_framework.response import Response

from tackapp.serializers import NotificationSerializer
from firebase_admin.messaging import Message, Notification, FCMOptions, AndroidConfig, APNSConfig, APNSFCMOptions, APNSPayload

logger = logging.getLogger()


class HealthCheck(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response()


class NotificationView(views.APIView):
    @extend_schema(request=NotificationSerializer, responses=NotificationSerializer)
    def post(self, request, *args, **kwargs):
        data = {
            "title": 'New Notification fired',
            "body": 'I just fired a new notification'
        }
        kwargs = {
            "content_available": True,
            'extra_kwargs': {"priority": "high", "mutable_content": True, 'notification': data},
        }
        # message = Message(
        #     notification=Notification(title="title", body="First one", image="url"),
        #     android=AndroidConfig(
        #         priority="high"
        #     ),
        #     apns=APNSConfig(
        #         fcm_options=APNSFCMOptions(
        #
        #         )
        #     ),
        #     fcm_options=FCMOptions(
        #         analytics_label={
        #             "priority": 10
        #         }
        #     )
        message = messaging.Message(
            notification=messaging.Notification(
                title='$GOOG up 1.43% on the day',
                body='$GOOG gained 11.80 points to close at 835.67, up 1.43% on the day.',
            ),
            android=messaging.AndroidConfig(
                ttl=datetime.timedelta(seconds=3600),
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='stock_ticker_update',
                    color='#f45342'
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(badge=42),
                    critical=True,
                    volume=1
                ),
            )
        )
            # data={
            #     "Nick": "Mario",
            #     "body": "great match!",
            #     "Room": "PortugalVSDenmark"
            # },

        serializer = NotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        devices = FCMDevice.objects.filter(user_id=serializer.validated_data["user"])
        logger.warning(f"{devices = }")
        # response = devices.send_message(message=message, sound='default', **kwargs)
        response = devices.send_message(message)
        logger.warning(f"{response = }")
        return Response()
