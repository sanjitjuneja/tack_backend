# Generated by Django 4.0.6 on 2022-07-28 13:22

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0005_alter_bankaccount_usd_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='usd_balance',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99999999)]),
        ),
    ]