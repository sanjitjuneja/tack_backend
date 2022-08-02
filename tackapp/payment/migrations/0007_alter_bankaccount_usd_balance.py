# Generated by Django 4.0.6 on 2022-07-30 08:15

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0006_alter_bankaccount_usd_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='usd_balance',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99999999)]),
        ),
    ]
