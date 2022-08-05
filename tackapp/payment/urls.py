from django.urls import path

from .views import *
from rest_framework import routers

# router = routers.SimpleRouter()
# router.register(r"tacks", TackViewset)

urlpatterns = [
    path(r"payment/refill/", AddBalance.as_view()),
    path(r"payment/withdrawal/", MoneyWithdrawal.as_view()),
    path(r"payment/add-payment-method/", AddCreditCard.as_view()),

    # path(r"payment/webhook/", pi_created),
    # path(r"payment/webhook2/", my_handler)

]
# urlpatterns = router.urls
