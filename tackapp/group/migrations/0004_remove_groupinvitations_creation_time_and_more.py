# Generated by Django 4.1 on 2022-08-16 09:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("group", "0003_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="groupinvitations",
            name="creation_time",
        ),
        migrations.RemoveField(
            model_name="groupinvitations",
            name="is_active",
        ),
    ]