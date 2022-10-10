from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import BankAccount, UserPaymentMethods, Fee, StripePaymentMethodsHolder, ServiceFee, Transaction
from .services import convert_to_decimal


class ReadOnlyMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BankAccount)
class BankAccountAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('id', 'user', 'human_readable_usd_balance', 'stripe_user', 'dwolla_user')
    search_fields = ('user__firstname', 'user__lastname', 'stripe_user', 'dwolla_user')
    search_help_text = "Search by User id, name, stripe id, dwolla id"
    ordering = ('id',)

    @admin.display(description="USD balance", ordering='usd_balance')
    def human_readable_usd_balance(self, obj: BankAccount):
        if obj.usd_balance is None:
            return "-"
        decimal_amount = convert_to_decimal(obj.usd_balance)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"


# @admin.register(UserPaymentMethods)
# class UserPaymentMethodsAdmin(ModelAdmin):
#     list_per_page = 50
#     list_display = ('bank_account', 'dwolla_payment_method')
#     search_fields = ('bank_account', 'dwolla_payment_method')
#     search_help_text = "Search by Bank account id, Dwolla method id"
#     ordering = ('id',)


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
class TransactionAdmin(AdminAdvancedFiltersMixin, ReadOnlyMixin, ModelAdmin):
    list_display = (
        'user',
        'human_readable_amount_requested',
        'human_readable_amount_with_fees',
        'human_readable_fee_difference',
        'human_readable_service_fee',
        'service_name',
        'action_type',
        'is_succeeded',
        'transaction_id',
    )
    list_filter = ('creation_time', 'service_name', 'action_type')
    advanced_filter_fields = (
        'amount_requested',
        'amount_with_fees',
        'service_fee',
        'fee_difference',
        'service_name',
        'action_type',
        'is_succeeded',
    )
    search_fields = ('user__first_name', 'user__last_name', 'transaction_id')
    search_help_text = "Search by User id, name, Transaction id"

    @admin.display(description="Requested", ordering='amount_requested')
    def human_readable_amount_requested(self, obj: Transaction):
        decimal_amount = convert_to_decimal(obj.amount_requested)
        if decimal_amount % 1:
            return f"${decimal_amount:.2f}"
        return f"${str(decimal_amount)}"

    @admin.display(description="Total", ordering='amount_with_fees')
    def human_readable_amount_with_fees(self, obj: Transaction):
        decimal_amount = convert_to_decimal(obj.amount_with_fees)
        if decimal_amount % 1:
            return f"${decimal_amount:.2f}"
        return f"${str(decimal_amount)}"

    @admin.display(description="Fee difference", ordering='fee_difference')
    def human_readable_fee_difference(self, obj: Transaction):
        if not obj.fee_difference:
            return "-"
        decimal_amount = convert_to_decimal(obj.fee_difference)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"

    @admin.display(description="Service fee", ordering='service_fee')
    def human_readable_service_fee(self, obj: Transaction):
        if not obj.service_fee:
            return "-"
        decimal_amount = convert_to_decimal(obj.service_fee)
        if decimal_amount % 1:
            return f"${decimal_amount:.2f}"
        return f"${str(decimal_amount)}"
