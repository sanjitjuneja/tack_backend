from django.urls import path

from .views import *
from rest_framework import routers

# router = routers.SimpleRouter()
# router.register(r"tacks", TackViewset)

urlpatterns = [
    path(r"payment/refill/", AddBalance.as_view()),
    path(r"payment/withdrawal/", MoneyWithdrawal.as_view()),
]
# urlpatterns = router.urls
