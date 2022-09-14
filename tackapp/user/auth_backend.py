import logging

from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import PasswordField
from fcm_django.models import FCMDevice

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from user.models import User

logger = logging.getLogger()


def create_firebase_device(device_fields, user):
    FCMDevice.objects.update_or_create(
        device_id=device_fields.get('device_id'),
        defaults={
            "name": device_fields.get('device_name'),
            "user": user,
            "registration_id": device_fields.get('firebase_token'),
            "type": device_fields.get('device_type'),
        }
    )


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
        self.fields["device_id"] = serializers.CharField(required=False)
        self.fields["firebase_token"] = serializers.CharField(required=False)
        self.fields["device_type"] = serializers.CharField(required=False)
        self.fields["device_name"] = serializers.CharField(required=False)

    def validate(self, attrs):
        credentials = {
            'phone_number': attrs.get("phone_number"),
            'password': attrs.get("password")
        }
        try:
            if isinstance(credentials['phone_number'], str):
                credentials['phone_number'] = credentials['phone_number'].lower()

            logger.warning(f"{credentials = }")
            if "@" in credentials["phone_number"]:
                user = User.objects.get(
                    email=credentials["phone_number"]
                )
                credentials['phone_number'] = user.phone_number
                logger.warning(f"Inside if: {user = }")
            else:
                user = User.objects.get(
                    phone_number=credentials["phone_number"]
                )
                logger.warning(f"Inside else: {user = }")

        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )
        else:
            data = super().validate(credentials)
            if all(name in attrs for name in ("device_id", "device_type")):
                create_firebase_device(attrs, user)
            return data
