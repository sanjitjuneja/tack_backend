from stats.user.service import UserStats
from stats.utils import _setup_filters
from group.models import Group


def get_user_stats_dict(user_stats: UserStats, group: Group = None):
    filters = _setup_filters(group=group)
    return {
        "avg_total_user_balance": user_stats.get_avg_total_user_balance(**filters),
        "sum_total_user_balance": user_stats.get_sum_total_user_balance(**filters),
        "users_visits_per_hour": user_stats.get_user_visits_count_per_hour(**filters)
    }
