# Generated by Django 4.1 on 2022-08-05 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tack", "0014_tack_accepted_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="offer",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
