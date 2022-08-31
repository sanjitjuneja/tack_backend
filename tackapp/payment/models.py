from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint, Deferrable

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

    class Meta:
        db_table = "bank_account"
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"


class UserPaymentMethods(models.Model):
    bank_account = models.ForeignKey("payment.BankAccount", on_delete=models.CASCADE)
    dwolla_payment_method = models.CharField(max_length=64)
    is_primary = models.BooleanField(default=False)

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
    fee_percent = models.DecimalField(
        default=3.00,
        decimal_places=2,
        max_digits=4,
        validators=(percent_validator,)
    )
    fee_min = models.PositiveIntegerField(default=25)
    fee_max = models.PositiveIntegerField(default=1500)

    class Meta:
        db_table = "fees"
        verbose_name = "Fee"
        verbose_name_plural = "Fees"


class DwollaRemovedAccount(models.Model):
    dwolla_id = models.UUIDField()

    class Meta:
        db_table = "dwolla_removed_accounts"
        verbose_name = "Dwolla removed account"
        verbose_name_plural = "Dwolla removed accounts"
