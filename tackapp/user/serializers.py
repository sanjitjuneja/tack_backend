from rest_framework import serializers
from .models import User


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
            "balance"
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
