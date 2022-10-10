from group.models import Group
from stats.user.service import UserStats


def get_user_stats_dict(user_stats: UserStats, group: Group = None):
    return {
        "avg_total_user_balance": user_stats.get_avg_total_user_balance(),
        "sum_total_user_balance": user_stats.get_sum_total_user_balance(),
    }
