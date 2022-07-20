from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from user.serializers import UserSerializer
from core.validators import password_validator


class SMSSendSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()


class TwilioUserRegistrationSerializer(serializers.Serializer):
    uuid = serializers.CharField(max_length=36)
    user = UserSerializer()


class LoginSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    password = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, required=True, validators=[password_validator]
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
    sms_code = serializers.CharField(max_length=6)
    uuid = serializers.CharField(max_length=36)
