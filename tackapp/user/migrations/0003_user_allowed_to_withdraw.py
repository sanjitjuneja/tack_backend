# Generated by Django 4.0.7 on 2022-10-03 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_user_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='allowed_to_withdraw',
            field=models.BooleanField(default=True),
        ),
    ]
