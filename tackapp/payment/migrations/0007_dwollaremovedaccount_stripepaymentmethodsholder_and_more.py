# Generated by Django 4.1 on 2022-08-31 09:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("djstripe", "0011_alter_invoiceitem_tax_rates_and_more"),
        ("payment", "0006_alter_bankaccount_dwolla_access_token_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DwollaRemovedAccount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("dwolla_id", models.UUIDField()),
            ],
            options={
                "verbose_name": "Dwolla removed account",
                "verbose_name_plural": "Dwolla removed accounts",
                "db_table": "dwolla_removed_accounts",
            },
        ),
        migrations.CreateModel(
            name="StripePaymentMethodsHolder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_primary_deposit", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "Stripe Payment method holder",
                "verbose_name_plural": "Stripe Payment methods holder",
                "db_table": "stripe_pm_holder",
            },
        ),
        migrations.AddField(
            model_name="userpaymentmethods",
            name="is_primary_deposit",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userpaymentmethods",
            name="is_primary_withdraw",
            field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name="userpaymentmethods",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_primary_deposit", True)),
                fields=("bank_account",),
                name="bank_account_one_primary_deposit",
            ),
        ),
        migrations.AddConstraint(
            model_name="userpaymentmethods",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_primary_withdraw", True)),
                fields=("bank_account",),
                name="bank_account_one_primary_withdraw",
            ),
        ),
        migrations.AddField(
            model_name="stripepaymentmethodsholder",
            name="stripe_pm",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="djstripe.paymentmethod",
                unique=True,
            ),
        ),
    ]
