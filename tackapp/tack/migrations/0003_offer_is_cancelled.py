# Generated by Django 4.0.7 on 2022-09-14 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tack', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='is_cancelled',
            field=models.BooleanField(default=False),
        ),
    ]
