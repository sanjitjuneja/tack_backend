from rest_framework import serializers

from core.validators import password_validator
from payment.serializers import BankAccountSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[password_validator]
    )

    def create(self, validated_data):
        print(f"{validated_data = }")
        instance = User.objects.create_user(
            phone_number=validated_data.pop("phone_number"),
            password=validated_data.pop("password"),
            first_name=validated_data.pop("first_name"),
            last_name=validated_data.pop("last_name"),
            # email=validated_data.pop("email")
        )
        return instance

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "active_group",
            "email",
        )
        read_only_fields = ("active_group",)
        extra_kwargs = {"password": {"write_only": True}}


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "tacks_rating",
            "tacks_amount",
        )


class UserDetailSerializer(serializers.ModelSerializer):
    bankaccount = BankAccountSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "tacks_rating",
            "tacks_amount",
            "bankaccount",
            "email",
            "profile_picture",
            "phone_number",
            "birthday",
            "active_group",
        )
        read_only_fields = (
            "id",
            "tacks_rating",
            "tacks_amount",
            "bankaccount",
            "active_group",
            "phone_number",
            "profile_picture",
            "active_group"
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "password", "phone_number")
        read_only_fields = ("id", "phone_number")
