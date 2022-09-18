from rest_framework import views
from rest_framework.response import Response


class HealthCheck(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response()
