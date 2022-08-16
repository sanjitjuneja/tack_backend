from django.urls import path

from .views import *
from rest_framework import routers

# router = routers.SimpleRouter()
# router.register(r"tacks", TackViewset)

urlpatterns = [
    path("payment/refill-stripe/", AddBalanceStripe.as_view()),
    # path(r"payment/withdraw/", DwollaMoneyWithdraw.as_view()),
    path("payment/get-payment-methods/", GetUserPaymentMethods.as_view()),
    path("payment/get-withdraw-methods/", GetUserWithdrawMethods.as_view()),
    path("payment/add-payment-method/", AddPaymentMethod.as_view()),
    path("payment/get-link-token/", GetLinkToken.as_view()),
    path("payment/add-withdraw-method/", AddUserWithdrawMethod.as_view())
]
# urlpatterns = router.urls
