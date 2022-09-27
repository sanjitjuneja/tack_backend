from rest_framework import serializers

nullable_user_fields = ('tacker', 'runner', 'user', 'member', 'owner')


class CustomSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in nullable_user_fields:
            try:
                if not data[field]:
                    data[field] = {
                        "id": 0,
                        "first_name": "Deleted",
                        "last_name": "User",
                        "tacks_rating": "0.00",
                        "tacks_amount": 0
                    }
            except KeyError:
                pass
        return data


class CustomModelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in nullable_user_fields:
            try:
                if not data[field]:
                    data[field] = {
                        "id": 0,
                        "first_name": "Deleted",
                        "last_name": "User",
                        "tacks_rating": "0.00",
                        "tacks_amount": 0
                    }
            except KeyError:
                pass
        return data
