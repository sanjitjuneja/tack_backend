# Generated by Django 4.0.6 on 2022-08-02 12:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0008_bankaccount_stripe_user_userpaymentmethods'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='userpaymentmethods',
            table='payment_methods',
        ),
    ]