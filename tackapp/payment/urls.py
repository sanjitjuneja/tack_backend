from django.urls import path

from .views import *

urlpatterns = [
    path("payment/refill-stripe/", AddBalanceStripe.as_view()),
    path("payment/refill-dwolla/", AddBalanceDwolla.as_view()),
    path("payment/get-payment-methods/", GetUserPaymentMethods.as_view()),
    path("payment/get-withdraw-methods/", GetUserWithdrawMethods.as_view()),
    path("payment/add-payment-method/", AddPaymentMethod.as_view()),
    path("payment/get-link-token/", GetLinkToken.as_view()),
    path("payment/add-withdraw-method/", AddUserWithdrawMethod.as_view()),
    path("payment/withdraw/", DwollaMoneyWithdraw.as_view())
]
