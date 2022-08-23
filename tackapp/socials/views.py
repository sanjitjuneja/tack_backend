from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from drf_yasg.utils import swagger_auto_schema
from rest_framework import views
from rest_framework.response import Response
from uuid import uuid4
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.base.exceptions import TwilioRestException

from user.models import User
from user.serializers import UserDetailSerializer
from .sms_service import twilio_client
from .serializers import *
from .services import generate_sms_code
from .models import PhoneVerification
from core.choices import SMSType


class TwilioSendMessage(views.APIView):
    """View for sending SMS to user for subsequent verification"""

    # @swagger_auto_schema(request_body=SMSSendSerializer, responses={200: "uuid", 400: "error_message"})
    @extend_schema(request=SMSSendSerializer, responses=SMSSendSerializer)
    def post(self, request):
        serializer = SMSSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uuid = uuid4()
        phone_number = serializer.validated_data["phone_number"]
        sms_code = generate_sms_code()

        try:
            User.objects.get(phone_number=phone_number)
            return Response({"error": "code", "message": "User already exists"})
        except User.DoesNotExist:
            pass

        try:
            message_sid = twilio_client.send_signup_message(phone_number, sms_code)
        except TwilioRestException:
            return Response({"error": "Twilio service temporarily unavailable"}, status=503)

        sms_type = SMSType.SIGNUP
        PhoneVerification(
            uuid=uuid,
            user=None,
            phone_number=phone_number,
            sms_code=sms_code,
            message_sid=message_sid,
            sms_type=sms_type,
        ).save()

        return Response({"uuid": uuid}, status=200)


class TwilioUserRegistration(views.APIView):
    """View for User registration with phone number"""

    # @swagger_auto_schema(request_body=TwilioUserRegistrationSerializer)
    @extend_schema(
        request=TwilioUserRegistrationSerializer,
        responses={
            200: TwilioUserRegistrationSerializer, 400: {"message": "text"}})
    @transaction.atomic
    def post(self, request):
        serializer = TwilioUserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            # Creating new User with given info
            # and updating user_id in PhoneVerification model
            phv = PhoneVerification.objects.get(uuid=serializer.validated_data["uuid"])
            if not phv.is_verified:
                return Response(
                    {"message": "SMS code wasn't verified in previous step"}, status=400
                )
            user_data = serializer.validated_data["user"].copy() | {"phone_number": phv.phone_number.as_e164}
            user_serializer = UserSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)

            try:
                User.objects.get(email=serializer.validated_data["user"]["email"])
                return Response({"error": "code", "message": "User with given email already exists"}, status=400)
            except User.DoesNotExist:
                pass

            user = user_serializer.save()

            phv.user = user
            phv.save()
            return Response({"user": UserDetailSerializer(user).data}, status=200)
        except ObjectDoesNotExist:
            return Response({"message": "invalid uuid"}, status=400)


# class Login(views.APIView):
#     """Login view"""
#
#     # @swagger_auto_schema(request_body=LoginSerializer)
#     @extend_schema(request=LoginSerializer, responses=LoginSerializer)
#     def post(self, request):
#         phone_number = request.data.get("phone_number")
#         password = request.data.get("password")
#         user = authenticate(request, phone_number=phone_number, password=password)
#         if user is not None:
#             login(request, user)
#             return Response({"message": "Successfully authorized"})
#         else:
#             return Response({"message": "Invalid credentials"}, status=401)


# class Logout(views.APIView):
#     """Logout view"""
#
#     @extend_schema(request=serializers.Serializer, responses=serializers.Serializer)
#     def get(self, request):
#         if request.user.is_authenticated:
#             logout(request)
#             return Response({"message": "Successfully logged out"}, status=200)
#         else:
#             return Response({"message": "User not logged in"}, status=200)


class PasswordRecoverySendMessage(views.APIView):
    """View for sending SMS for subsequent password recovery"""

    # @swagger_auto_schema(request_body=SMSSendSerializer)
    @extend_schema(request=SMSSendSerializer, responses=SMSSendSerializer)
    def post(self, request):
        serializer = SMSSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uuid = uuid4()
        phone_number = serializer.validated_data["phone_number"]
        sms_code = generate_sms_code()
        sms_type = SMSType.RECOVERY

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"error": "code", "message": "User with the given phone number is not found"}, status=400
            )
        except TwilioRestException:
            return Response({"error": "Twilio service temporarily unavailable"}, status=503)

        message_sid = twilio_client.send_recovery_message(phone_number, sms_code)
        PhoneVerification(
            uuid=uuid,
            user=user,
            phone_number=phone_number,
            sms_code=sms_code,
            message_sid=message_sid,
            sms_type=sms_type,
        ).save()
        return Response(
            {"uuid": uuid, "phone_number": phone_number.as_e164}, status=200
        )


class PasswordRecoveryChange(views.APIView):
    """View for changing user password through recovery"""

    # @swagger_auto_schema(request_body=PasswordRecoveryChangeSerializer)
    @extend_schema(request=PasswordRecoveryChangeSerializer, responses={200: {"message": "text"}})
    def post(self, request):
        if request.user.is_authenticated:
            return Response({"message": "Can not recover password when authorized"})
        serializer = PasswordRecoveryChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uuid = serializer.validated_data["uuid"]

        try:
            phv = PhoneVerification.objects.get(uuid=uuid)
        except PhoneVerification.DoesNotExist:
            return Response({"error": "code", "message": "Row with given uuid does not exist"}, status=400)
        if not phv.is_verified:
            return Response({"message": "You did not verify your SMS code"}, status=400)
        user = phv.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        # # Login after password change
        # user = authenticate(
        #     request,
        #     phone_number=user.phone_number,
        #     password=serializer.validated_data["new_password"],
        # )
        # login(request, user)

        return Response(
            {"message": "Password successfully changed"}, status=200
        )


class PasswordChange(views.APIView):
    """View for changing user password manually"""

    @extend_schema(request=PasswordChangeSerializer, responses=PasswordChangeSerializer)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "User is not autheticated"}, status=401)

        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not request.user.check_password(old_password):
            return Response({"message": "Incorrect password"})
        if old_password == new_password:
            return Response({"message": "Your passwords are identical"})

        request.user.set_password(new_password)
        request.user.save()
        refresh = RefreshToken.for_user(request.user)
        # Login after password change
        # user = authenticate(
        #     request, phone_number=request.user.phone_number, password=new_password
        # )

        return Response(
            {
                "message": "Password successfully changed",
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=200
        )


class VerifySMSCode(views.APIView):
    """View for verification SMS code"""

    @extend_schema(request=VerifySMSCodeSerializer, responses=VerifySMSCodeSerializer)
    def post(self, request):
        serializer = VerifySMSCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uuid = serializer.validated_data["uuid"]
        sms_code = serializer.validated_data["sms_code"]
        expiration_time = timedelta(hours=6)
        try:
            phv = PhoneVerification.objects.get(uuid=uuid)
            if timezone.now() > phv.creation_time + expiration_time:
                return Response({"message": "Verification period expired"}, status=400)
            if sms_code != phv.sms_code:
                return Response({"message": "SMS code is wrong"}, status=400)
            phv.is_verified = True
            phv.save()
        except ObjectDoesNotExist:
            return Response({"message": "Row with given uuid is not found"}, status=400)

        return Response({"message": "Verified", "uuid": uuid}, status=200)
