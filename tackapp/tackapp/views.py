from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.response import Response


class HealthCheck(views.APIView):
    @extend_schema(request=None, responses=None)
    def get(self, request, *args, **kwargs):
        return Response()
