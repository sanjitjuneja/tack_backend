# Generated by Django 4.0.7 on 2022-09-12 16:55

import core.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usd_balance', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99999999)])),
                ('stripe_user', models.CharField(max_length=64)),
                ('dwolla_user', models.CharField(blank=True, default=None, max_length=64, null=True)),
                ('dwolla_access_token', models.CharField(blank=True, default=None, max_length=128, null=True)),
            ],
            options={
                'verbose_name': 'Bank Account',
                'verbose_name_plural': 'Bank Accounts',
                'db_table': 'bank_account',
            },
        ),
        migrations.CreateModel(
            name='Fee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fee_percent_stripe', models.DecimalField(decimal_places=2, default=3.0, max_digits=4, validators=[core.validators.percent_validator])),
                ('fee_min_stripe', models.PositiveIntegerField(default=25)),
                ('fee_max_stripe', models.PositiveIntegerField(default=1500)),
                ('fee_percent_dwolla', models.DecimalField(decimal_places=2, default=0, max_digits=4, validators=[core.validators.percent_validator])),
                ('fee_min_dwolla', models.PositiveIntegerField(default=0)),
                ('fee_max_dwolla', models.PositiveIntegerField(default=1500)),
                ('max_loss', models.PositiveIntegerField(default=4000)),
            ],
            options={
                'verbose_name': 'Fee',
                'verbose_name_plural': 'Fees',
                'db_table': 'fees',
            },
        ),
        migrations.CreateModel(
            name='ServiceFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_percent', models.DecimalField(decimal_places=2, default=2.9, max_digits=4, validators=[core.validators.percent_validator])),
                ('stripe_const_sum', models.PositiveIntegerField(default=30)),
                ('dwolla_percent', models.DecimalField(decimal_places=2, default=5.0, max_digits=4, validators=[core.validators.percent_validator])),
                ('dwolla_const_sum', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='StripePaymentMethodsHolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_primary', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Stripe Payment method holder',
                'verbose_name_plural': 'Stripe Payment methods holder',
                'db_table': 'stripe_pm_holder',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_requested', models.PositiveIntegerField()),
                ('amount_with_fees', models.PositiveIntegerField()),
                ('service_fee', models.PositiveIntegerField()),
                ('is_dwolla', models.BooleanField(default=False)),
                ('is_stripe', models.BooleanField(default=False)),
                ('transaction_id', models.CharField(max_length=255)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('is_succeeded', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='UserPaymentMethods',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dwolla_payment_method', models.CharField(max_length=64)),
                ('plaid_account_id', models.CharField(max_length=128)),
                ('is_primary', models.BooleanField(default=False)),
                ('dwolla_access_token', models.CharField(blank=True, default=None, max_length=128, null=True)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payment.bankaccount')),
            ],
            options={
                'verbose_name': 'Payment method',
                'verbose_name_plural': 'Payment methods',
                'db_table': 'payment_methods',
            },
        ),
    ]
