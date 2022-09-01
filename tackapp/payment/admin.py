from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import BankAccount, UserPaymentMethods, Fee, StripePaymentMethodsHolder


@admin.register(BankAccount)
class BankAccountAdmin(ModelAdmin):
    list_display = ('user', 'usd_balance', 'stripe_user', 'dwolla_user')


@admin.register(UserPaymentMethods)
class UserPaymentMethodsAdmin(ModelAdmin):
    list_display = ('bank_account', 'dwolla_payment_method')


@admin.register(Fee)
class FeeAdmin(ModelAdmin):
    list_display = ('fee_percent', 'fee_min', 'fee_max')


@admin.register(StripePaymentMethodsHolder)
class StripePaymentMethodsHolderAdmin(ModelAdmin):
    list_display = ('stripe_pm', 'is_primary')
