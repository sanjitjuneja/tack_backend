# Generated by Django 4.0.7 on 2022-08-10 14:46

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
            ],
            options={
                'verbose_name': 'Bank Account',
                'verbose_name_plural': 'Bank Accounts',
                'db_table': 'bank_account',
            },
        ),
        migrations.CreateModel(
            name='UserPaymentMethods',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method', models.CharField(max_length=64)),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payment.bankaccount')),
            ],
            options={
                'verbose_name': 'Payment method',
                'verbose_name_plural': 'Payment methods',
                'db_table': 'payment_methods',
            },
        ),
    ]
