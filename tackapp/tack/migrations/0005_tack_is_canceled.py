# Generated by Django 4.1 on 2022-08-26 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tack", "0004_alter_tack_runner"),
    ]

    operations = [
        migrations.AddField(
            model_name="tack",
            name="is_canceled",
            field=models.BooleanField(default=False),
        ),
    ]