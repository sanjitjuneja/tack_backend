# Generated by Django 4.1 on 2022-08-30 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tack", "0006_alter_tack_status"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="offer",
            name="unique_runner_for_tack",
        ),
        migrations.AddConstraint(
            model_name="offer",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_active", True)),
                fields=("tack", "runner"),
                name="unique_runner_for_tack",
            ),
        ),
    ]
