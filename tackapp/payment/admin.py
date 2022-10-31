from advanced_filters.admin import AdminAdvancedFiltersMixin
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.models import LogEntry

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


@admin.register(UserPaymentMethods)
class UserPaymentMethodsAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ('bank_account', 'dwolla_payment_method')
    search_fields = ('bank_account', 'dwolla_payment_method')
    search_help_text = "Search by Bank account id, Dwolla method id"
    ordering = ('id',)


@admin.register(Fee)
class FeeAdmin(ModelAdmin):
    list_display = (
        'human_readable_max_loss',
        'human_readable_fee_percent_stripe',
        'human_readable_fee_min_stripe',
        'human_readable_fee_max_stripe',
        'human_readable_fee_percent_dwolla',
        'human_readable_fee_min_dwolla',
        'human_readable_fee_max_dwolla'
    )

    @admin.display(description="Max 24h loss", ordering='max_loss')
    def human_readable_max_loss(self, obj: Fee):
        if obj.max_loss is None:
            return "-"
        decimal_amount = convert_to_decimal(obj.max_loss)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"

    @admin.display(description="Fee percent Stripe", ordering='fee_percent_stripe')
    def human_readable_fee_percent_stripe(self, obj: Fee):
        if obj.fee_percent_stripe is None:
            return "-"
        return f"{obj.fee_percent_stripe} %"

    @admin.display(description="Fee min Stripe", ordering='fee_min_stripe')
    def human_readable_fee_min_stripe(self, obj: Fee):
        if obj.fee_min_stripe is None:
            return "-"
        decimal_amount = convert_to_decimal(obj.fee_min_stripe)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"

    @admin.display(description="Fee max Stripe", ordering='fee_max_stripe')
    def human_readable_fee_max_stripe(self, obj: Fee):
        if obj.fee_max_stripe is None:
            return "-"
        decimal_amount = convert_to_decimal(obj.fee_max_stripe)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"

    @admin.display(description="Fee percent Dwolla", ordering='fee_percent_dwolla')
    def human_readable_fee_percent_dwolla(self, obj: Fee):
        if obj.fee_percent_dwolla is None:
            return "-"
        return f"{obj.fee_percent_dwolla} %"

    @admin.display(description="Fee min Dwolla", ordering='fee_min_dwolla')
    def human_readable_fee_min_dwolla(self, obj: Fee):
        if obj.fee_min_dwolla is None:
            return "-"
        decimal_amount = convert_to_decimal(obj.fee_min_dwolla)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"

    @admin.display(description="Fee max Dwolla", ordering='fee_max_dwolla')
    def human_readable_fee_max_dwolla(self, obj: Fee):
        if obj.fee_max_dwolla is None:
            return "-"
        decimal_amount = convert_to_decimal(obj.fee_max_dwolla)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"


@admin.register(StripePaymentMethodsHolder)
class StripePaymentMethodsHolderAdmin(ModelAdmin):
    list_display = ('stripe_pm', 'is_primary')


@admin.register(ServiceFee)
class ServiceFeeAdmin(ModelAdmin):
    list_display = (
        'human_readable_fee_stripe_percent',
        'human_readable_stripe_const_sum',
        'human_readable_dwolla_percent',
        'human_readable_dwolla_const_sum'
    )

    @admin.display(description="Service Fee percent Stripe", ordering='stripe_percent')
    def human_readable_fee_stripe_percent(self, obj: ServiceFee):
        if obj.stripe_percent is None:
            return "-"
        return f"{obj.stripe_percent} %"

    @admin.display(description="Stripe const amount", ordering='stripe_const_sum')
    def human_readable_stripe_const_sum(self, obj: ServiceFee):
        if obj.stripe_const_sum is None:
            return "-"
        decimal_amount = convert_to_decimal(obj.stripe_const_sum)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"

    @admin.display(description="Service Fee percent Stripe", ordering='dwolla_percent')
    def human_readable_dwolla_percent(self, obj: ServiceFee):
        if obj.dwolla_percent is None:
            return "-"
        return f"{obj.dwolla_percent} %"

    @admin.display(description="Dwolla const amount", ordering='dwolla_const_sum')
    def human_readable_dwolla_const_sum(self, obj: ServiceFee):
        if obj.dwolla_const_sum is None:
            return "-"
        decimal_amount = convert_to_decimal(obj.dwolla_const_sum)
        if decimal_amount.is_signed():
            if decimal_amount % 1:
                return f"-${abs(decimal_amount):.2f}"
            return f"-${str(abs(decimal_amount))}"
        else:
            if decimal_amount % 1:
                return f"${decimal_amount:.2f}"
            return f"${str(decimal_amount)}"


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


@admin.register(LogEntry)
class LogEntryAdmin(ModelAdmin):
    list_per_page = 50
    list_display = ("id", "action_time", "action_flag", "user", "content_type", "object_id")
    list_display_links = ("id", "action_time")
