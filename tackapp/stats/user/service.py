from datetime import timedelta
from django.db.models import Avg, Sum, Q
from django.utils import timezone

from stats.utils import _setup_filters
from payment.models import BankAccount
from stats.models import UserVisits
from group.models import Group
from user.models import User


class UserStats:
    def __init__(self):
        pass

    def get_avg_total_user_balance(self, group: Group = None):
        filters = _setup_filters(groupmembers__group=group)
        users = User.objects.filter(
            **filters,
        )
        return BankAccount.objects.filter(
            user__in=users
        ).aggregate(
            avg_user_balance=Avg('usd_balance')
        )["avg_user_balance"]

    def get_sum_total_user_balance(self, group: Group = None):
        filters = _setup_filters(groupmembers__group=group)
        users = User.objects.filter(
            **filters,
        )
        return BankAccount.objects.filter(
            user__in=users
        ).aggregate(
            sum_user_balance=Sum('usd_balance')
        )["sum_user_balance"]

    def get_user_visits_count_per_hour(self, group: Group = None) -> int:
        """
        Collect  information about attendance by users of the application
        """
        filters: dict = _setup_filters(groupmembers__group=group)
        users: list[User] = User.objects.filter(
            **filters,
        )
        count_users_visits: int = UserVisits.objects.filter(
            Q(
                user__in=users
            )
            &
            Q(
                timestamp__gte=timezone.now() - timedelta(hours=1)
            )
        ).count()
        return count_users_visits
