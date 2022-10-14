from django.db import models
from user.models import User


class GlobalStats(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    num_tacks_created_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_tacks_accepted_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_tacks_completed_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_tacks_created_by_tackers_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_tacks_completed_by_runners_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None
    )
    avg_price_last_hour = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_tackers_time_estimation = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_first_offer_time = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    runner_tacker_ratio = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_num_offers_before_accept = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    num_allowed_counteroffers = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    avg_total_user_balance = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    sum_total_user_balance = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    total_sum_fees_we_paid_last_hour = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    num_card_deposits_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_dg_wallets_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_banks_deposits_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_bank_withdraws_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    avg_amount_per_card_deposit_w_fees = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_amount_per_dg_wallet_deposit_w_fees = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_amount_per_bank_deposit_w_fees = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_amount_per_card_deposit_wo_fees = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_amount_per_dg_wallet_deposit_wo_fees = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_amount_per_bank_deposit_wo_fees = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_amount_per_bank_withdraw_w_fees = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_amount_per_bank_withdraw_wo_fees = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )

    class Meta:
        db_table = "global_stats"
        verbose_name = "Global Stats"
        verbose_name_plural = "Global Stats"


class GroupStats(models.Model):
    timestamp = models.DateTimeField(
        auto_now_add=True
    )
    group = models.ForeignKey(
        "group.Group", blank=True, null=True, on_delete=models.SET_NULL, default=None
    )
    num_tacks_created_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_tacks_accepted_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_tacks_completed_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_tacks_created_by_tackers_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    num_tacks_completed_by_runners_last_hour = models.PositiveIntegerField(
        blank=True, null=True, default=None
    )
    avg_price_last_hour = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_tackers_time_estimation = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_first_offer_time = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    runner_tacker_ratio = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    avg_num_offers_before_accept = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    num_allowed_counteroffers = models.PositiveIntegerField(
        blank=True, null=True, default=None,
    )
    avg_total_user_balance = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    sum_total_user_balance = models.DecimalField(
        blank=True, null=True, default=None, max_digits=8, decimal_places=2
    )
    users_visits_per_hour = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "group_stats"
        verbose_name = "Group Stats"
        verbose_name_plural = "Group Stats"


class UserVisits(models.Model):
    user = models.ForeignKey(to=User, verbose_name='User visits', related_name='visits', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_visits"
        verbose_name = "User Visits"
        verbose_name_plural = "User Visits"