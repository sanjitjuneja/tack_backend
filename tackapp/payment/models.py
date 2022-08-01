from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


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

    class Meta:
        db_table = "bank_account"
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"


class UserPaymentMethods(models.Model):
    bank_account = models.ForeignKey("payment.BankAccount", on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=64)

    class Meta:
        db_table = "payments"
        verbose_name = "Payment method"
        verbose_name_plural = "Payment methods"
