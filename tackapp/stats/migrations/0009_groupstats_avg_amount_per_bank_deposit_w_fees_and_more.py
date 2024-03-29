# Generated by Django 4.0.8 on 2022-10-26 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0008_globalstats_avg_first_offer_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupstats',
            name='avg_amount_per_bank_deposit_w_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='avg_amount_per_bank_deposit_wo_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='avg_amount_per_card_deposit_w_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='avg_amount_per_card_deposit_wo_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='avg_amount_per_dg_wallet_deposit_w_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='avg_amount_per_dg_wallet_deposit_wo_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='num_banks_deposits_last_hour',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='num_card_deposits_last_hour',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='num_dg_wallets_last_hour',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='groupstats',
            name='total_sum_fees_we_paid_last_hour',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
    ]
