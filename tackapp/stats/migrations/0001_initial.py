# Generated by Django 4.0.8 on 2022-10-12 12:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('group', '0007_alter_group_collect_stats'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('num_tacks_created_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_tacks_accepted_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_tacks_completed_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_tacks_created_by_tackers_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_tacks_completed_by_runners_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('avg_price_last_hour', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_tackers_time_estimation', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_first_offer_time', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('runner_tacker_ratio', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_num_offers_before_accept', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('num_allowed_counteroffers', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('avg_total_user_balance', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('sum_total_user_balance', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('total_sum_fees_we_paid_last_hour', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('num_card_deposits_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_dg_wallets_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_banks_deposits_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_bank_withdraws_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('avg_amount_per_card_deposit_w_fees', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_amount_per_dg_wallet_deposit_w_fees', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_amount_per_bank_deposit_w_fees', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_amount_per_card_deposit_wo_fees', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_amount_per_dg_wallet_deposit_wo_fees', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_amount_per_bank_deposit_wo_fees', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_amount_per_bank_withdraw_w_fees', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_amount_per_bank_withdraw_wo_fees', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
            ],
            options={
                'verbose_name': 'Global Stats',
                'verbose_name_plural': 'Global Stats',
                'db_table': 'global_stats',
            },
        ),
        migrations.CreateModel(
            name='GroupStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('num_tacks_created_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_tacks_accepted_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_tacks_completed_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_tacks_created_by_tackers_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('num_tacks_completed_by_runners_last_hour', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('avg_price_last_hour', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_tackers_time_estimation', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_first_offer_time', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('runner_tacker_ratio', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('avg_num_offers_before_accept', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('num_allowed_counteroffers', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('avg_total_user_balance', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('sum_total_user_balance', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=8, null=True)),
                ('group', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='group.group')),
            ],
            options={
                'verbose_name': 'Group Stats',
                'verbose_name_plural': 'Group Stats',
                'db_table': 'group_stats',
            },
        ),
    ]
