# Generated by Django 4.0.7 on 2022-09-14 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0003_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='description',
            field=models.CharField(blank=True, default=None, max_length=256, null=True),
        ),
    ]
