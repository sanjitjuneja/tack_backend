from django.db.models import Avg, Sum

from group.models import Group
from payment.models import BankAccount
from stats.utils import _setup_filters
from user.models import User


class UserStats:
    def __init__(self):
        pass

    def get_avg_total_user_balance(self, group: Group = None):
        filters = _setup_filters(groupmembers__in=group)
        users = User.objects.filter(
            **filters,
        )
        return BankAccount.objects.filter(
            user__in=users
        ).aggregate(
            avg_user_balance=Avg('usd_balance')
        )["avg_user_balance"]

    def get_sum_total_user_balance(self, group: Group = None):
        filters = _setup_filters(groupmembers__in=group)
        users = User.objects.filter(
            **filters,
        )
        return BankAccount.objects.filter(
            user__in=users
        ).aggregate(
            sum_user_balance=Avg('usd_balance')
        )["sum_user_balance"]
