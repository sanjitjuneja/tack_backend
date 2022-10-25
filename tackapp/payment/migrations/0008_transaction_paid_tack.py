# Generated by Django 4.0.8 on 2022-10-19 09:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tack', '0008_tack_start_completion_time'),
        ('payment', '0007_alter_transaction_service_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='paid_tack',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tack.tack'),
        ),
    ]