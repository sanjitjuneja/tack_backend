# Generated by Django 4.0.7 on 2022-08-08 07:39

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0004_review_unique_user_for_tack'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='creation_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]