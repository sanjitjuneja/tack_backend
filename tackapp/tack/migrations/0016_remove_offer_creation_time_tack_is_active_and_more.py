# Generated by Django 4.0.7 on 2022-08-08 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tack', '0015_offer_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='offer',
            name='creation_time',
        ),
        migrations.AddField(
            model_name='tack',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='populartack',
            name='estimation_time_seconds',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='tack',
            name='estimation_time_seconds',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
    ]