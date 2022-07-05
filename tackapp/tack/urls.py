from django.urls import path

from .views import *
from rest_framework import routers

# router = routers.SimpleRouter()
# router.register(r'health-check', HealthCheckView.as_view(), basename="HealthCheckView")

urlpatterns = [
    path(r"health-check/", HealthCheckView.as_view()),
]
