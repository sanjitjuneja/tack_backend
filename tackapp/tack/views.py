from rest_framework import views
from rest_framework.response import Response


class HealthCheckView(views.APIView):
    def get(self, request):
        return Response(status=200)
