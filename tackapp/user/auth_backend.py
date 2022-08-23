from django.db.models import Q

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from user.models import User


class CustomJWTSerializer(TokenObtainPairSerializer):
    username_field = "phone_number"

    def validate(self, attrs):
        credentials = {
            'phone_number': attrs.get("phone_number"),
            'password': attrs.get("password")
        }

        if type(credentials['phone_number']) is str:
            credentials['phone_number'] = credentials['phone_number'].lower()

        try:
            user = User.objects.get(
                Q(phone_number=credentials["phone_number"]) |
                Q(email=credentials["phone_number"])
            )
            if user:
                credentials['phone_number'] = user.phone_number
        except User.DoesNotExist:
            pass

        return super().validate(credentials)
