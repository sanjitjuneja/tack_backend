from datetime import timedelta

from django.db.models import Avg, Sum
from django.utils import timezone

from group.models import Group
from payment.models import Transaction, BankAccount
from tack.models import Tack
from user.models import User

created_tacks_last_hour = Tack.objects.filter(
    creation_time__gte=timezone.now() - timedelta(hours=1)
)
accepted_tacks_last_hour = Tack.objects.filter(
    accepted_time__gte=timezone.now() - timedelta(hours=1)
)
completed_tacks_last_hour = Tack.objects.filter(
    completion_time__gte=timezone.now() - timedelta(hours=1)
)
active_users_last_week = User.objects.filter(
    last_login__gte=timezone.now() - timedelta(days=7)
)
transactions_last_hour = Transaction.objects.filter(
    creation_time__gte=timezone.now() - timedelta(hours=1),
)
collected_groups = Group.active.filter(
    collect_stats=True
)
bank_accounts = BankAccount.objects.all()
bank_accounts_stats = bank_accounts.aggregate(
    avg_user_balance=Avg('usd_balance'),
    sum_user_balance=Sum('usd_balance'),
)
