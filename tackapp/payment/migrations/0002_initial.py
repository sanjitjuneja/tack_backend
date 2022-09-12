# Generated by Django 4.0.7 on 2022-09-12 17:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payment', '0001_initial'),
        ('djstripe', '0011_alter_invoiceitem_tax_rates_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='stripepaymentmethodsholder',
            name='stripe_pm',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='djstripe.paymentmethod'),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='userpaymentmethods',
            constraint=models.UniqueConstraint(condition=models.Q(('is_primary', True)), fields=('bank_account',), name='bank_account_one_primary'),
        ),
    ]
