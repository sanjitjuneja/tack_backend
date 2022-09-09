# Generated by Django 4.0.7 on 2022-09-09 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0005_delete_dwollaremovedaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpaymentmethods',
            name='dwolla_access_token',
            field=models.CharField(blank=True, default=None, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='userpaymentmethods',
            name='plaid_account_id',
            field=models.CharField(default='default', max_length=128),
            preserve_default=False,
        ),
    ]
