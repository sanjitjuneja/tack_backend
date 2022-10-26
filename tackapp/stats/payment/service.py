from datetime import timedelta

from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone

from core.choices import PaymentService, PaymentAction
from group.models import Group
from payment.models import Transaction
from stats.utils import _setup_filters


class PaymentStats:
    def __init__(
            self,
            group: Group = None
    ):
        self.payment_data_last_hour = self.get_payment_stats(group)

    def get_payment_stats(self, group: Group = None):
        filters = _setup_filters(paid_tack__group=group)
        return Transaction.objects.filter(
            creation_time__gte=timezone.now() - timedelta(hours=1),
            **filters
        ).aggregate(
            sum_fees_paid=Sum(
                'fee_difference'
            ),
            num_card_deposits=Count(
                'id',
                filter=Q(
                    service_name=PaymentService.STRIPE,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            num_dg_wallets_deposits=Count(
                'id',
                filter=Q(
                    service_name=PaymentService.DIGITAL_WALLET,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            num_banks_deposits=Count(
                'id',
                filter=Q(
                    service_name=PaymentService.DWOLLA,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            avg_amount_per_card_deposit_w_fees=Avg(
                'amount_with_fees',
                filter=Q(
                    service_name=PaymentService.STRIPE,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            avg_amount_per_dg_wallet_deposit_w_fees=Avg(
                'amount_with_fees',
                filter=Q(
                    service_name=PaymentService.DIGITAL_WALLET,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            avg_amount_per_bank_deposit_w_fees=Avg(
                'amount_with_fees',
                filter=Q(
                    service_name=PaymentService.DWOLLA,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            avg_amount_per_card_deposit_wo_fees=Avg(
                'amount_requested',
                filter=Q(
                    service_name=PaymentService.STRIPE,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            avg_amount_per_dg_wallet_deposit_wo_fees=Avg(
                'amount_requested',
                filter=Q(
                    service_name=PaymentService.DIGITAL_WALLET,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            avg_amount_per_bank_deposit_wo_fees=Avg(
                'amount_requested',
                filter=Q(
                    service_name=PaymentService.DWOLLA,
                    action_type=PaymentAction.DEPOSIT,
                )
            ),
            num_bank_withdraws=Count(
                'id',
                filter=Q(
                    service_name=PaymentService.STRIPE,
                    action_type=PaymentAction.WITHDRAW,
                )
            ),
            avg_amount_per_bank_withdraw_w_fees=Avg(
                'amount_with_fees',
                filter=Q(
                    service_name=PaymentService.DWOLLA,
                    action_type=PaymentAction.WITHDRAW,
                )
            ),
            avg_amount_per_bank_withdraw_wo_fees=Avg(
                'amount_requested',
                filter=Q(
                    service_name=PaymentService.DWOLLA,
                    action_type=PaymentAction.WITHDRAW,
                )
            ),
        )

    def get_total_sum_fees_we_paid_last_hour(self):
        return self.payment_data_last_hour["sum_fees_paid"] or 0

    def get_num_card_deposits_last_hour(self):
        return self.payment_data_last_hour["num_card_deposits"] or 0

    def get_num_dg_wallets_last_hour(self):
        return self.payment_data_last_hour["num_dg_wallets_deposits"] or 0

    def get_num_banks_deposits_last_hour(self):
        return self.payment_data_last_hour["num_banks_deposits"] or 0

    def get_num_bank_withdraws_last_hour(self):
        return self.payment_data_last_hour["num_bank_withdraws"] or 0

    def get_avg_amount_per_card_deposit_w_fees(self):
        return self.payment_data_last_hour["avg_amount_per_card_deposit_w_fees"] or 0

    def get_avg_amount_per_dg_wallet_deposit_w_fees(self):
        return self.payment_data_last_hour["avg_amount_per_dg_wallet_deposit_w_fees"] or 0

    def get_avg_amount_per_bank_deposit_w_fees(self):
        return self.payment_data_last_hour["avg_amount_per_bank_deposit_w_fees"] or 0

    def get_avg_amount_per_card_deposit_wo_fees(self):
        return self.payment_data_last_hour["avg_amount_per_card_deposit_wo_fees"] or 0

    def get_avg_amount_per_dg_wallet_deposit_wo_fees(self):
        return self.payment_data_last_hour["avg_amount_per_dg_wallet_deposit_wo_fees"] or 0

    def get_avg_amount_per_bank_deposit_wo_fees(self):
        return self.payment_data_last_hour["avg_amount_per_bank_deposit_wo_fees"] or 0

    def get_avg_amount_per_bank_withdraw_w_fees(self):
        return self.payment_data_last_hour["avg_amount_per_bank_withdraw_w_fees"] or 0

    def get_avg_amount_per_bank_withdraw_wo_fees(self):
        return self.payment_data_last_hour["avg_amount_per_bank_withdraw_wo_fees"] or 0
