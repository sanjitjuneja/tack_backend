from django.core.validators import DecimalValidator, MinValueValidator, MaxValueValidator
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
    # stripe_user

    class Meta:
        db_table = "bank_account"
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
