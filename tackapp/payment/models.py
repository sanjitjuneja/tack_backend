from django.core.validators import DecimalValidator, MinValueValidator, MaxValueValidator
from django.db import models


class BankAccount(models.Model):
    user = models.OneToOneField("user.User", on_delete=models.CASCADE)
    usd_balance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[
            DecimalValidator(8, 2),
            MinValueValidator(0),
            MaxValueValidator(999_999.99),
        ])

    class Meta:
        db_table = "bank_account"
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
