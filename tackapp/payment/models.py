import djstripe.models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint, Deferrable
from djstripe.models import PaymentMethod as dsPaymentMethod

from core.validators import percent_validator


class BankAccount(models.Model):
    user = models.OneToOneField("user.User", on_delete=models.CASCADE)
    usd_balance = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(999_999_99),
        ),
        default=0
    )
    stripe_user = models.CharField(max_length=64)
    dwolla_user = models.CharField(max_length=64, null=True, blank=True, default=None)
    dwolla_access_token = models.CharField(max_length=128, null=True, blank=True, default=None)

    def __str__(self):
        return f"{str(self.user)}: {self.usd_balance / 100:.2f} $"

    class Meta:
        db_table = "bank_account"
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"


class UserPaymentMethods(models.Model):
    bank_account = models.ForeignKey("payment.BankAccount", on_delete=models.CASCADE)
    dwolla_payment_method = models.CharField(max_length=64)
    plaid_account_id = models.CharField(max_length=128)
    is_primary = models.BooleanField(default=False)
    dwolla_access_token = models.CharField(max_length=128, null=True, blank=True, default=None)

    class Meta:
        db_table = "payment_methods"
        verbose_name = "Payment method"
        verbose_name_plural = "Payment methods"
        constraints = [
            UniqueConstraint(
                fields=(
                    "bank_account",
                ),
                condition=Q(
                    is_primary=True
                ),
                name='bank_account_one_primary',
            )
        ]


class Fee(models.Model):
    fee_percent_stripe = models.DecimalField(
        default=3.00,
        decimal_places=2,
        max_digits=4,
        validators=(percent_validator,))
    fee_min_stripe = models.PositiveIntegerField(default=25)
    fee_max_stripe = models.PositiveIntegerField(default=1500)
    fee_percent_dwolla = models.DecimalField(
        default=0,
        decimal_places=2,
        max_digits=4,
        validators=(percent_validator,))
    fee_min_dwolla = models.PositiveIntegerField(default=0)
    fee_max_dwolla = models.PositiveIntegerField(default=1500)
    max_loss = models.PositiveIntegerField(default=4000)

    class Meta:
        db_table = "fees"
        verbose_name = "Fee"
        verbose_name_plural = "Fees"


class StripePaymentMethodsHolder(models.Model):
    stripe_pm = models.OneToOneField(dsPaymentMethod, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "stripe_pm_holder"
        verbose_name = "Stripe Payment method holder"
        verbose_name_plural = "Stripe Payment methods holder"


class Transaction(models.Model):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE)
    amount_requested = models.PositiveIntegerField()
    amount_with_fees = models.PositiveIntegerField()
    service_fee = models.PositiveIntegerField()
    is_dwolla = models.BooleanField(default=False)
    is_stripe = models.BooleanField(default=False)
    is_deposit = models.BooleanField(default=True)
    transaction_id = models.CharField(max_length=255)
    creation_time = models.DateTimeField(auto_now_add=True)
    is_succeeded = models.BooleanField(default=False)


class ServiceFee(models.Model):
    stripe_percent = models.DecimalField(
        default=2.90,
        decimal_places=2,
        max_digits=4,
        validators=(percent_validator,))
    stripe_const_sum = models.PositiveIntegerField(default=30)
    dwolla_percent = models.DecimalField(
        default=5.00,
        decimal_places=2,
        max_digits=4,
        validators=(percent_validator,))
    dwolla_const_sum = models.PositiveIntegerField(default=0)
