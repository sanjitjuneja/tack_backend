# Generated by Django 4.0.7 on 2022-09-13 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpaymentmethods',
            name='plaid_account_id',
            field=models.CharField(blank=True, default=None, max_length=128, null=True),
        ),
    ]
