from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import BankAccount, UserPaymentMethods, Fee, StripePaymentMethodsHolder, ServiceFee, Transaction


class ReadOnlyMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BankAccount)
class BankAccountAdmin(ModelAdmin):
    list_display = ('user', 'usd_balance', 'stripe_user', 'dwolla_user')


@admin.register(UserPaymentMethods)
class UserPaymentMethodsAdmin(ModelAdmin):
    list_display = ('bank_account', 'dwolla_payment_method')


@admin.register(Fee)
class FeeAdmin(ModelAdmin):
    list_display = (
        'max_loss',
        'fee_percent_stripe',
        'fee_min_stripe',
        'fee_max_stripe',
        'fee_percent_dwolla',
        'fee_min_dwolla',
        'fee_max_dwolla'
    )


@admin.register(StripePaymentMethodsHolder)
class StripePaymentMethodsHolderAdmin(ModelAdmin):
    list_display = ('stripe_pm', 'is_primary')


@admin.register(ServiceFee)
class ServiceFeeAdmin(ModelAdmin):
    list_display = ('stripe_percent', 'stripe_const_sum', 'dwolla_percent', 'dwolla_const_sum')


@admin.register(Transaction)
class TransactionAdmin(ReadOnlyMixin, ModelAdmin):
    list_display = (
        'user',
        'is_stripe',
        'is_dwolla',
        'transaction_id',
        'amount_requested',
        'amount_with_fees',
        'service_fee'
    )
    list_filter = ('creation_time',)
    search_fields = ('user', 'transaction_id')
