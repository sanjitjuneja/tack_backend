from datetime import timedelta

from celery import shared_task
from django.db.models import Subquery, QuerySet, Count, OuterRef, Avg, Sum, F, ExpressionWrapper, BooleanField, Q
from django.utils import timezone

from core.choices import TackStatus, PaymentService, PaymentAction
from payment.models import BankAccount, Transaction
from tack.models import Tack
from user.models import User


@shared_task
def collect_stats():
    hourly_created_tacks = Tack.objects.filter(
        creation_time_gte=timezone.now() - timedelta(hours=1)
    ).aggregate(
        count=Count('id'),
        avg_price=Avg('price')
    )
    hourly_accepted_tacks = Tack.objects.filter(
        accepted_time_gte=timezone.now() - timedelta(hours=1)
    )
    hourly_completed_tacks = Tack.objects.filter(
        completion_time__gte=timezone.now() - timedelta(hours=1)
    )
    active_users = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=7)
    )
    tackers = list()
    for user in active_users:
        if user.tack_tacker.count() >= 1:
            tackers.append(user.id)
    num_tacks_created_by_tackers = Tack.objects.filter(
        tacker__in=tackers
    ).count()

    runners = list()
    for user in active_users:
        if user.tack_runner.count() >= 3:
            tackers.append(user.id)
    num_tacks_created_by_tackers = Tack.objects.filter(
        runner__in=runners
    ).count()

    avg_time_estimation_sec = hourly_created_tacks.filter(
        tacker__in=tackers
    ).aggregate(avg_time_estimation_sec=Avg('time_estimation_seconds'))

    avg_acceptance_time = hourly_accepted_tacks.filter(
        accepted_time__isnull=False
    ).aggregate(Avg('accepted_time'))

    runner_tacker_ratio = len(runners) / len(tackers) if len(tackers) else len(runners)

    offer_num_list = list()
    for tack in hourly_accepted_tacks:
        offer_num = tack.offer_set.count()
        offer_num_list.append(offer_num)
    avg_offer_num_before_match = sum(offer_num_list) / len(offer_num_list) if len(offer_num_list) else 0

    num_allowed_counter_offers_tacks = hourly_created_tacks.filter(
        allow_counter_offer=True
    ).count()

    ba_stats = BankAccount.objects.aggregate(
        avg_user_balance=Avg('usd_balance'),
        sum_user_balance=Sum('usd_balance'),
    )
    avg_user_balance = ba_stats["avg_user_balance"]
    sum_user_balance = ba_stats["sum_user_balance"]

    hourly_transactions = Transaction.objects.filter(
        creation_time__gte=timezone.now() - timedelta(hours=1),
    ).aggregate(
        num_card_deposits=Count(
            'id',
            filter=Q(
                service_name=PaymentService.STRIPE,
                action_type=PaymentAction.DEPOSIT,
            )
        ),
        num_dg_wallets_depostits=Count(
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
        avg_amount_per_card_deposit=Avg(
            'amount_with_fees',
            filter=Q(
                service_name=PaymentService.STRIPE,
                action_type=PaymentAction.DEPOSIT,
            )
        ),
        avg_amount_per_dg_wallet_deposit=Avg(
            'amount_with_fees',
            filter=Q(
                service_name=PaymentService.DIGITAL_WALLET,
                action_type=PaymentAction.DEPOSIT,
            )
        ),
        avg_amount_per_bank_deposit=Avg(
            'amount_with_fees',
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
        avg_amount_per_bank_withdraw=Avg(
            'amount_with_fees',
            filter=Q(
                service_name=PaymentService.DWOLLA,
                action_type=PaymentAction.WITHDRAW,
            )
        ),
    )

