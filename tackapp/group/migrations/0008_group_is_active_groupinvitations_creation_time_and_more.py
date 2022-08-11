# Generated by Django 4.0.7 on 2022-08-08 08:43

from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0007_groupmutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='groupinvitations',
            name='creation_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groupinvitations',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='group',
            name='invitation_link',
            field=models.CharField(default=uuid.uuid4, max_length=36, unique=True),
        ),
    ]