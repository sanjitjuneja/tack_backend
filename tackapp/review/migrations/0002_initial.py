# Generated by Django 4.0.7 on 2022-09-12 16:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('review', '0001_initial'),
        ('tack', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='tack',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_tack', to='tack.tack'),
        ),
    ]
