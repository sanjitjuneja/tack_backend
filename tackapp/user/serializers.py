from rest_framework import serializers

from payment.serializers import BankAccountSerializer
from .models import User
from payment.models import BankAccount


class UserSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = User.objects.create_user(
            phone_number=validated_data.pop("phone_number"),
            password=validated_data.pop("password"),
            first_name=validated_data.pop("first_name"),
            last_name=validated_data.pop("last_name"))
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
