from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from fcm_django.models import FCMDevice
from rest_framework import views
from rest_framework.response import Response

from tackapp.serializers import NotificationSerializer


class HealthCheck(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response()


class Notification(views.APIView):
    @extend_schema(request=NotificationSerializer, responses=NotificationSerializer)
    def post(self, request, *args, **kwargs):
        serializer = NotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        FCMDevice.objects.filter(user_id=NotificationSerializer)
        return Response()
