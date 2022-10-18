import logging
import time

from celery import shared_task

from stats.payment.utils import get_payment_stats_dict
from stats.models import GlobalStats, GroupStats
from stats.tack.utils import get_tack_stats_dict
from stats.user.utils import get_user_stats_dict
from stats.payment.service import PaymentStats
from stats.user.service import UserStats
from stats.tack.service import TackStats
from stats.global_queries import (
    created_tacks_last_hour,
    accepted_tacks_last_hour,
    completed_tacks_last_hour,
    active_users_last_week
)
from group.models import Group

logger = logging.getLogger('django')


@shared_task
def collect_stats():
    """Main task for collecting statistics for grafana"""

    tack_stats = TackStats(
        created_tacks_last_hour=created_tacks_last_hour,
        accepted_tacks_last_hour=accepted_tacks_last_hour,
        completed_tacks_last_hour=completed_tacks_last_hour,
        active_users_last_week=active_users_last_week,
    )
    user_stats = UserStats()
    payment_stats = PaymentStats()

    start_time = time.time()
    global_tack_stats_dict = get_tack_stats_dict(tack_stats)
    global_user_stats_dict = get_user_stats_dict(user_stats)
    global_payment_stats_dict = get_payment_stats_dict(payment_stats)
    global_stats_dict = global_tack_stats_dict | global_user_stats_dict | global_payment_stats_dict
    logger.info(f"{global_stats_dict = }")
    GlobalStats.objects.create(**global_stats_dict)
    logger.info(f"Global stats took ~ {round(time.time() - start_time, 2)} seconds")

    start_time = time.time()
    collected_group_for_stats = Group.objects.filter(collect_stats=True)
    group_stats_list = []
    for group in collected_group_for_stats:
        group_tack_stats_dict = get_tack_stats_dict(tack_stats, group=group)
        group_user_stats_dict = get_user_stats_dict(user_stats, group=group)
        group_stats_dict = {"group": group} | group_tack_stats_dict | group_user_stats_dict
        logger.info(f"{group_stats_dict = }")
        group_stats_list.append(GroupStats(**group_stats_dict))
    GroupStats.objects.bulk_create(group_stats_list)
    logger.info(f"Group stats took ~ {round(time.time() - start_time, 2)} seconds")

    logger.info("Stats collection finished")
