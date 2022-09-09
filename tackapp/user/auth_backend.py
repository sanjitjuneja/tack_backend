# from .models import User
# from django.db.models import Q
#
#
# class AuthBackend(object):
#     supports_object_permissions = True
#     supports_anonymous_user = False
#     supports_inactive_user = False
#
#     def get_user(self, user_id):
#         try:
#             return User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return None
#
#     def authenticate(self, phone_number, password):
#         try:
#             user = User.objects.get(
#                 Q(username=phone_number) | Q(email=phone_number) | Q(phone_number=phone_number)
#             )
#         except User.DoesNotExist:
#             return None
#
#         return user if user.check_password(password) else None
from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer, PasswordField
from fcm_django.models import FCMDevice

from django.contrib.auth import authenticate, get_user_model
# from django.utils.translation import ugettext as _
# from rest_framework import serializers
#
# from rest_framework_jwt.settings import api_settings


# User = get_user_model()
# jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
# jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
# jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
# jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from user.models import User


class CustomJWTSerializer(TokenObtainPairSerializer):
    username_field = "phone_number"
    device_id = "device_id"
    firebase_token = "firebase_token"
    device_name = "device_name"
    device_type = "device_type"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields["password"] = PasswordField()
        self.fields["device_id"] = serializers.CharField()
        self.fields["firebase_token"] = serializers.CharField()
        self.fields["device_type"] = serializers.CharField()
        self.fields["device_name"] = serializers.CharField()

    def validate(self, attrs):
        credentials = {
            'phone_number': attrs.get("phone_number"),
            'password': attrs.get("password")
        }
        # if "@" in credentials["phone_number"]:
        #     filter_ = Q(...)
        # else:
        #     filter_ = Q(...)

        try:
            user = User.objects.get(
                Q(phone_number=credentials["phone_number"]) |
                Q(email=credentials["phone_number"])
            )
            if user:
                credentials['phone_number'] = user.phone_number
        except User.DoesNotExist:
            pass
        else:
            self.create_device(attrs, user)
        return super().validate(credentials)

    @staticmethod
    def create_device(device_fields, user):
        # FCMDevice.objects.create(
        #     name=device_fields.get('device_name'),
        #     active=True,
        #     user=user,
        #     registration_id=device_fields.get('firebase_token'),
        #     type=device_fields.get('device_type'),
        #     device_id=device_fields.get('device_id')
        # )
        FCMDevice.objects.update_or_create(
            device_id=device_fields.get('device_id'),
            defaults={
                "name": device_fields.get('device_name'),
                # "active": True,
                "user": user,
                "registration_id": device_fields.get('firebase_token'),
                "type": device_fields.get('device_type'),
            }
        )


