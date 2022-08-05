# Generated by Django 4.0.6 on 2022-07-28 13:20

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0004_remove_bankaccount_stripe_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='usd_balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8, validators=[django.core.validators.DecimalValidator(8, 2), django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(999999.99)]),
        ),
    ]