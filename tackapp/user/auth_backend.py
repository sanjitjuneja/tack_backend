import logging
from datetime import timedelta

from django.core.exceptions import MultipleObjectsReturned
from django.utils import timezone
from rest_framework import serializers, exceptions, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import PasswordField
from fcm_django.models import FCMDevice

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from core.exceptions import TooManyAttemptsError, MultipleAccountsError
from socials.models import TimeoutSettings, FailedLoginAttempts
from user.models import User

logger = logging.getLogger("django")


def create_firebase_device(device_fields, user):
    FCMDevice.objects.update_or_create(
        device_id=device_fields.get('device_id'),
        defaults={
            "name": device_fields.get('device_name'),
            "user": user,
            "registration_id": device_fields.get('firebase_token'),
            "type": device_fields.get('device_type'),
            "active": True
        }
    )


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (TooManyAttemptsError, MultipleAccountsError) as e:
            return Response(
                {
                    "error": e.error,
                    "message": e.message
                },
                status=e.status)
        except AuthenticationFailed as e:
            return Response(
                {
                    "error": "Ux1",
                    "message": "Wrong authentication credentials"
                },
                status=400)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


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
            if "@" in credentials["phone_number"]:
                user = User.objects.get(
                    email=credentials["phone_number"]
                )
                credentials['phone_number'] = user.phone_number
                logger.debug(f"Inside if: {user = }")
            else:
                user = User.objects.get(
                    phone_number=credentials["phone_number"]
                )
                logger.debug(f"Inside else: {user = }")

            if is_failed_attempt(attrs, user):
                logger.debug("inside first is_failed_attempt")
                raise TooManyAttemptsError(
                    error="Sx12",
                    message="Too many unsuccessful sing-in attempts. Try again later",
                    status=400
                )
        except User.DoesNotExist:
            FailedLoginAttempts.objects.create(
                device_id=attrs.get("device_id"),
                device_type=attrs.get("device_type"),
                device_name=attrs.get("device_name"),
                credentials=credentials["phone_number"]
            )
            if is_failed_attempt(attrs, None):
                logger.debug("inside first is_failed_attempt")
                raise TooManyAttemptsError(
                    error="Sx12",
                    message="Too many unsuccessful sing-in attempts. Try again later",
                    status=400
                )
            logger.debug(f"Failed login attempt with {credentials['phone_number']}")
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        except MultipleObjectsReturned as e:
            raise MultipleAccountsError(
                error="Sx13",
                message=("Multiple users with given credentials found. ",
                         "Please, contact our support."),
                status=400
            )
        else:
            logger.debug(f"INSIDE ELSE STATEMENT JWT SERIALIZER")
            try:
                data = super().validate(credentials)
            except AuthenticationFailed as e:
                FailedLoginAttempts.objects.create(
                    user=user,
                    device_id=attrs.get("device_id"),
                    device_type=attrs.get("device_type"),
                    device_name=attrs.get("device_name"),
                    credentials=credentials["phone_number"]
                )
                raise exceptions.AuthenticationFailed(
                    self.error_messages["no_active_account"],
                    "no_active_account",
                )
            else:
                if all(name in attrs for name in ("device_id", "device_type")):
                    create_firebase_device(attrs, user)
                return data


def is_failed_attempt(serializer_fields: dict, user: User | None) -> bool:
    timeout_settings = TimeoutSettings.objects.all().last()
    time_window_minutes = timeout_settings.signin_time_window_minutes if timeout_settings else 60
    max_signin_attempts_per_time_window = timeout_settings.signin_max_attempts_per_window if timeout_settings else 10

    if device_id := serializer_fields.get("device_id"):
        failed_attempts = FailedLoginAttempts.objects.filter(
            device_id=device_id,
            timestamp__gte=timezone.now() - timedelta(minutes=time_window_minutes)
        )
    elif user:
        logger.debug(f"elif user: {user = }")
        failed_attempts = FailedLoginAttempts.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(minutes=time_window_minutes)
        )
    else:
        logger.debug(f"else {serializer_fields.get('phone_number') = }")
        failed_attempts = FailedLoginAttempts.objects.filter(
            credentials=serializer_fields.get("phone_number"),
            timestamp__gte=timezone.now() - timedelta(minutes=time_window_minutes)
        )
    if failed_attempts.count() > max_signin_attempts_per_time_window:
        return True
    return False
