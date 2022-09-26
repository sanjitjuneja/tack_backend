import logging
from datetime import timedelta

import dwollav2
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from uuid import uuid4
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.base.exceptions import TwilioRestException

from user.models import User
from user.serializers import UserDetailSerializer
from .sms_service import twilio_client
from .serializers import *
from .services import generate_sms_code
from .models import PhoneVerification, TimeoutSettings
from core.choices import SMSType


logger = logging.getLogger('django')


class TwilioSendMessage(views.APIView):
    """View for sending SMS to user for subsequent verification"""

    @extend_schema(request=SMSSendSerializer, responses=SMSSendSerializer)
    def post(self, request):
        serializer = SMSSendSerializer(data=request.data)
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
        phone_number = serializer.validated_data["phone_number"]

        timeout_settings = TimeoutSettings.objects.all().last()
        time_window_minutes = timeout_settings.signup_time_window_minutes or 60
        max_signup_attempts_per_time_window = timeout_settings.signup_max_attempts_per_window or 3

        if PhoneVerification.objects.filter(
            phone_number=phone_number,
            creation_time__gte=timezone.now() - timedelta(minutes=time_window_minutes)
        ).count() > max_signup_attempts_per_time_window:
            return Response(
                {
                    "error": "Sx1",
                    "message": "Too many signup attempts. Try again later."
                },
                status=400)

        uuid = uuid4()
        sms_code = generate_sms_code()

        try:
            User.objects.get(phone_number=phone_number)
            return Response(
                {
                    "error": "Ux3",
                    "message": "User already exists"
                },
                status=400)
        except User.DoesNotExist:
            pass

        try:
            message_sid = twilio_client.send_signup_message(phone_number, sms_code)
        except TwilioRestException:
            return Response(
                {
                    "error": "Ox2",
                    "message": "Twilio service temporarily unavailable"
                },
                status=503)

        PhoneVerification(
            uuid=uuid,
            user=None,
            phone_number=phone_number,
            sms_code=sms_code,
            message_sid=message_sid,
            sms_type=SMSType.SIGNUP,
        ).save()

        return Response({"uuid": uuid}, status=200)


class TwilioUserRegistration(views.APIView):
    """View for User registration with phone number"""

    @extend_schema(
        request=TwilioUserRegistrationSerializer,
        responses={
            200: UserDetailSerializer, 400: {"message": "text"}})
    @transaction.atomic
    def post(self, request):
        serializer = TwilioUserRegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            logger.error(f"socials.views.TwilioUserRegistration {e = }")
            return Response(
                {
                    "error": "Ux2",
                    "meesage": "User with given email already exists"
                },
                status=400)

        try:
            # Creating new User with given info
            # and updating user_id in PhoneVerification model
            phv = PhoneVerification.objects.get(uuid=serializer.validated_data["uuid"])
            if not phv.is_verified:
                return Response(
                    {
                        "error": "Sx2",
                        "message": "SMS code wasn't verified in previous step"
                    },
                    status=400)
            user_data = serializer.validated_data["user"].copy() | {"phone_number": phv.phone_number.as_e164}
            user_serializer = UserSerializer(data=user_data)
            try:
                user_serializer.is_valid(raise_exception=True)
            except ValidationError as e:
                return Response(
                    {
                        "error": "Ox3",
                        "message": "Validation error. Some of the fields have invalid values",
                        "details": e.detail,
                    },
                    status=400)

            try:
                User.objects.get(email=serializer.validated_data["user"]["email"])
                return Response(
                    {
                        "error": "Ux2",
                        "message": "User with given email already exists"
                    },
                    status=400)
            except User.DoesNotExist:
                pass

            try:
                user = user_serializer.save()
            except dwollav2.InvalidResourceStateError as e:
                return Response(e.body)
            phv.user = user
            phv.save()
            return Response(UserDetailSerializer(user).data, status=200)
        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "Sx3",
                    "message": "invalid uuid"
                },
                status=400)


class PasswordRecoverySendMessage(views.APIView):
    """View for sending SMS for subsequent password recovery"""

    @extend_schema(request=SMSSendSerializer, responses=SMSSendSerializer)
    def post(self, request):
        serializer = SMSSendSerializer(data=request.data)
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
        phone_number = serializer.validated_data["phone_number"]
        timeout_settings = TimeoutSettings.objects.all().last()
        time_window_minutes = timeout_settings.signup_time_window_minutes or 60
        max_signup_attempts_per_time_window = timeout_settings.signup_max_attempts_per_window or 3

        if PhoneVerification.objects.filter(
                phone_number=phone_number,
                creation_time__gte=timezone.now() - timedelta(minutes=time_window_minutes)
        ).count() > max_signup_attempts_per_time_window:
            return Response(
                {
                    "error": "Sx1",
                    "message": "Too many password recovery attempts. Try again later."
                },
                status=400)

        uuid = uuid4()
        phone_number = serializer.validated_data["phone_number"]
        sms_code = generate_sms_code()

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {
                    "error": "Sx4",
                    "message": "User with the given phone number is not found"
                },
                status=400)
        except TwilioRestException:
            return Response(
                {
                    "error": "Ox2",
                    "message": "Twilio service temporarily unavailable"
                }, status=503)

        message_sid = twilio_client.send_recovery_message(phone_number, sms_code)
        PhoneVerification(
            uuid=uuid,
            user=user,
            phone_number=phone_number,
            sms_code=sms_code,
            message_sid=message_sid,
            sms_type=SMSType.RECOVERY,
        ).save()
        return Response(
            {
                "uuid": uuid,
                "phone_number": phone_number.as_e164
            },
            status=200)


class PasswordRecoveryChange(views.APIView):
    """View for changing user password through recovery"""

    @extend_schema(request=PasswordRecoveryChangeSerializer, responses={200: {"message": "text"}})
    def post(self, request):
        if request.user.is_authenticated:
            return Response(
                {
                    "error": "Sx5",
                    "message": "Can not recover password when authorized"
                },
                status=400)
        serializer = PasswordRecoveryChangeSerializer(data=request.data)
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
        uuid = serializer.validated_data["uuid"]

        try:
            phv = PhoneVerification.objects.get(uuid=uuid)
        except PhoneVerification.DoesNotExist:
            return Response(
                {
                    "error": "Sx3",
                    "message": "Row with given uuid does not exist"
                },
                status=400)
        if not phv.is_verified:
            return Response(
                {
                    "error": "Sx6",
                    "message": "You did not verify your SMS code"
                },
                status=400)
        user = phv.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(
            {
                "error": None,
                "message": "Password successfully changed"
            },
            status=200)


class PasswordChange(views.APIView):
    """View for changing user password manually"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(request=PasswordChangeSerializer, responses=PasswordChangeSerializer)
    def post(self, request):

        serializer = PasswordChangeSerializer(data=request.data)
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

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not request.user.check_password(old_password):
            return Response(
                {
                    "error": "Sx7",
                    "message": "Incorrect password"
                },
                status=400)
        if old_password == new_password:
            return Response(
                {
                    "error": "Sx8",
                    "message": "Your passwords are identical"
                },
                status=400)

        request.user.set_password(new_password)
        request.user.save()
        refresh = RefreshToken.for_user(request.user)
        return Response(
            {
                "error": None,
                "message": "Password successfully changed",
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            },
            status=200)


class VerifySMSCode(views.APIView):
    """View for verification SMS code"""

    @extend_schema(request=VerifySMSCodeSerializer, responses=VerifySMSCodeSerializer)
    def post(self, request):
        serializer = VerifySMSCodeSerializer(data=request.data)
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

        uuid = serializer.validated_data["uuid"]
        sms_code = serializer.validated_data["sms_code"]
        timeout_settings = TimeoutSettings.objects.all().last()
        activation_code_ttl_minutes = timeout_settings.signup_activation_code_ttl_minutes or 360

        expiration_time = timedelta(minutes=activation_code_ttl_minutes)
        try:
            phv = PhoneVerification.objects.get(uuid=uuid)
            # Check if activation code is not expired
            if timezone.now() > phv.creation_time + expiration_time:
                return Response(
                    {
                        "error": "Sx9",
                        "message": "Verification code expired"
                    },
                    status=400)
            if sms_code != phv.sms_code:
                return Response(
                    {
                        "error": "Sx10",
                        "message": "SMS code is wrong"
                    },
                    status=400)
            phv.is_verified = True
            phv.save()
        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "Sx3",
                    "message": "Row with given uuid is not found"
                },
                status=400)

        return Response(
            {
                "error": None,
                "message": "Verified",
                "uuid": uuid
            },
            status=200)
