from rest_framework import filters
from rest_framework import viewsets, mixins
from .serializers import *


class UsersViewset(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username', '=phone_number')
