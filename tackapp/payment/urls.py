from django.urls import path

from .views import *

urlpatterns = [
    path("payment/deposit-stripe/", AddBalanceStripe.as_view()),
    path("payment/deposit-dwolla/", AddBalanceDwolla.as_view()),
    path("payment/get-payment-methods/", GetUserPaymentMethods.as_view()),
    path("payment/get-withdraw-methods/", GetUserWithdrawMethods.as_view()),
    path("payment/add-payment-method/", AddPaymentMethod.as_view()),
    path("payment/get-link-token/", GetLinkToken.as_view()),
    path("payment/add-withdraw-method/", AddUserWithdrawMethod.as_view()),
    path("payment/withdraw/", DwollaMoneyWithdraw.as_view()),
    path("payment/get-stripe-pm-by-id/", GetPaymentMethodById.as_view()),
    path("payment/set-primary-method/", SetPrimaryPaymentMethod.as_view()),
    path("payment/detach-payment-method/", DetachPaymentMethod.as_view()),
    path("webhooks/dwolla/", DwollaWebhook.as_view()),
    path("payment/test-change-balance", TestChangeBankAccount.as_view())
]
