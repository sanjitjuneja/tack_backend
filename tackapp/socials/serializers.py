from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from core.custom_serializers import CustomSerializer
from user.serializers import UserSerializer, UserRegistrationSerializer
from core.validators import password_validator


class SMSSendSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(write_only=True)
    uuid = serializers.CharField(read_only=True)
    device_id = serializers.CharField(max_length=64, allow_null=True, write_only=True)


class TwilioUserRegistrationSerializer(CustomSerializer):
    uuid = serializers.CharField(max_length=36)
    user = UserRegistrationSerializer()


class LoginSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(write_only=True)
    password = serializers.CharField(write_only=True)
    message = serializers.CharField(read_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, required=True
    )
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[password_validator]
    )


class PasswordRecoveryChangeSerializer(serializers.Serializer):
    uuid = serializers.CharField(max_length=36)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[password_validator]
    )


class VerifySMSCodeSerializer(serializers.Serializer):
    sms_code = serializers.CharField(max_length=6, write_only=True)
    uuid = serializers.CharField(max_length=36, write_only=True)
    message = serializers.CharField(read_only=True)
