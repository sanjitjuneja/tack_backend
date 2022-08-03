from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import BankAccount, UserPaymentMethods


@admin.register(BankAccount)
class BankAccountAdmin(ModelAdmin):
    list_display = ['user', 'usd_balance', 'stripe_user']


@admin.register(UserPaymentMethods)
class UserPaymentMethodsAdmin(ModelAdmin):
    list_display = ['bank_account', 'payment_method']
