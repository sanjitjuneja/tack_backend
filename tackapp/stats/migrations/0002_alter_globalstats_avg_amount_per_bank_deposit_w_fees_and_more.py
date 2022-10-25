# Generated by Django 4.0.8 on 2022-10-14 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalstats',
            name='avg_amount_per_bank_deposit_w_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_amount_per_bank_deposit_wo_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_amount_per_bank_withdraw_w_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_amount_per_bank_withdraw_wo_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_amount_per_card_deposit_w_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_amount_per_card_deposit_wo_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_amount_per_dg_wallet_deposit_w_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_amount_per_dg_wallet_deposit_wo_fees',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_first_offer_time',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_num_offers_before_accept',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_price_last_hour',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_tackers_time_estimation',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='avg_total_user_balance',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='runner_tacker_ratio',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='sum_total_user_balance',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='globalstats',
            name='total_sum_fees_we_paid_last_hour',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='groupstats',
            name='avg_first_offer_time',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='groupstats',
            name='avg_num_offers_before_accept',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='groupstats',
            name='avg_price_last_hour',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='groupstats',
            name='avg_tackers_time_estimation',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='groupstats',
            name='avg_total_user_balance',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='groupstats',
            name='runner_tacker_ratio',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=14, null=True),
        ),
        migrations.AlterField(
            model_name='groupstats',
            name='sum_total_user_balance',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
    ]