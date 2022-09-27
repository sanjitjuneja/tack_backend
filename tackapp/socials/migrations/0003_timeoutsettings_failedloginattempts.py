# Generated by Django 4.0.7 on 2022-09-16 10:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('socials', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeoutSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signup_time_window_minutes', models.PositiveSmallIntegerField(default=60)),
                ('signup_max_attempts_per_window', models.PositiveSmallIntegerField(default=3)),
                ('signup_activation_code_ttl_minutes', models.PositiveSmallIntegerField(default=360)),
                ('signin_time_window_minutes', models.PositiveSmallIntegerField(default=60)),
                ('signin_max_attempts_per_window', models.PositiveSmallIntegerField(default=10)),
            ],
            options={
                'verbose_name': 'Timeout setting',
                'verbose_name_plural': 'Timeout settings',
                'db_table': 'timeout_settings',
            },
        ),
        migrations.CreateModel(
            name='FailedLoginAttempts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(blank=True, default=None, max_length=128, null=True)),
                ('device_type', models.CharField(blank=True, default=None, max_length=128, null=True)),
                ('device_name', models.CharField(blank=True, default=None, max_length=128, null=True)),
                ('credentials', models.CharField(max_length=128)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Failed login attempt',
                'verbose_name_plural': 'Failed login attempts',
                'db_table': 'failed_login_attempts',
            },
        ),
    ]
