# Generated by Django 4.0.7 on 2022-09-12 16:24

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PhoneVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('uuid', models.CharField(max_length=36)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('sms_code', models.CharField(max_length=6)),
                ('message_sid', models.CharField(max_length=64)),
                ('sms_type', models.CharField(choices=[('R', 'Recovery'), ('S', 'Signup')], max_length=2)),
                ('is_verified', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Verification',
                'verbose_name_plural': 'Verifications',
                'db_table': 'verifications',
            },
        ),
    ]
