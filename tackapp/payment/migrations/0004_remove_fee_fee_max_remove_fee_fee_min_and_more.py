# Generated by Django 4.0.7 on 2022-09-05 09:28

import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0003_servicefee_transaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fee',
            name='fee_max',
        ),
        migrations.RemoveField(
            model_name='fee',
            name='fee_min',
        ),
        migrations.RemoveField(
            model_name='fee',
            name='fee_percent',
        ),
        migrations.AddField(
            model_name='fee',
            name='fee_max_dwolla',
            field=models.PositiveIntegerField(default=1500),
        ),
        migrations.AddField(
            model_name='fee',
            name='fee_max_stripe',
            field=models.PositiveIntegerField(default=1500),
        ),
        migrations.AddField(
            model_name='fee',
            name='fee_min_dwolla',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='fee',
            name='fee_min_stripe',
            field=models.PositiveIntegerField(default=25),
        ),
        migrations.AddField(
            model_name='fee',
            name='fee_percent_dwolla',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4, validators=[core.validators.percent_validator]),
        ),
        migrations.AddField(
            model_name='fee',
            name='fee_percent_stripe',
            field=models.DecimalField(decimal_places=2, default=3.0, max_digits=4, validators=[core.validators.percent_validator]),
        ),
        migrations.AddField(
            model_name='fee',
            name='max_loss',
            field=models.PositiveIntegerField(default=4000),
        ),
    ]