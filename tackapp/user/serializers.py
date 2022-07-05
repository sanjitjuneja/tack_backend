from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = User.objects.create_user(
            username=validated_data.pop("username"),
            email=validated_data.pop("email"),
            password=validated_data.pop("password"),
            first_name=validated_data.pop("first_name"),
            last_name=validated_data.pop("last_name"),
            phone_number=validated_data.pop("phone_number"),
            birthday=validated_data.pop("birthday"),
        )
        return instance

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "birthday",
            "password",
        )
        extra_kwargs = {"password": {"write_only": True}}
