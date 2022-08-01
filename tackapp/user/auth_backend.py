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


from rest_framework_simplejwt.serializers import TokenObtainSerializer

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
    username_field = "phone or email"

    def validate(self, attrs):
        credentials = {
            'phone_number': attrs.get("phone_number"),
            'password': attrs.get("password")
        }

        user_obj = User.objects.filter(
            phone_number=credentials["phone_number"]).first() or \
                   User.objects.filter(email=credentials["phone_number"]).first()
        print(user_obj)
        if user_obj:
            credentials['phone_number'] = user_obj.phone_number

        return super().validate(credentials)