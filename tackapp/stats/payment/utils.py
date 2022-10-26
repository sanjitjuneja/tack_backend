from group.models import Group
from stats.payment.service import PaymentStats
from stats.utils import _setup_filters


def get_payment_stats_dict(payment_stats: PaymentStats, *, group: Group = None):
    values_dict = {
        "total_sum_fees_we_paid_last_hour": payment_stats.get_total_sum_fees_we_paid_last_hour(),
        "num_card_deposits_last_hour": payment_stats.get_num_card_deposits_last_hour(),
        "num_dg_wallets_last_hour": payment_stats.get_num_dg_wallets_last_hour(),
        "num_banks_deposits_last_hour": payment_stats.get_num_banks_deposits_last_hour(),
        "num_bank_withdraws_last_hour": payment_stats.get_num_bank_withdraws_last_hour(),
        "avg_amount_per_card_deposit_w_fees": payment_stats.get_avg_amount_per_card_deposit_w_fees(),
        "avg_amount_per_dg_wallet_deposit_w_fees": payment_stats.get_avg_amount_per_dg_wallet_deposit_w_fees(),
        "avg_amount_per_bank_deposit_w_fees": payment_stats.get_avg_amount_per_bank_deposit_w_fees(),
        "avg_amount_per_card_deposit_wo_fees": payment_stats.get_avg_amount_per_card_deposit_wo_fees(),
        "avg_amount_per_dg_wallet_deposit_wo_fees": payment_stats.get_avg_amount_per_dg_wallet_deposit_wo_fees(),
        "avg_amount_per_bank_deposit_wo_fees": payment_stats.get_avg_amount_per_bank_deposit_wo_fees(),
        "avg_amount_per_bank_withdraw_w_fees": payment_stats.get_avg_amount_per_bank_withdraw_w_fees(),
        "avg_amount_per_bank_withdraw_wo_fees": payment_stats.get_avg_amount_per_bank_withdraw_wo_fees(),
    }
    if group:
        del values_dict["num_bank_withdraws_last_hour"]
        del values_dict["avg_amount_per_bank_withdraw_w_fees"]
        del values_dict["avg_amount_per_bank_withdraw_wo_fees"]

    return values_dict
