import logging
import time
from datetime import timedelta

import django
from celery import shared_task
from django.db import models
from django.db.models import F
from django.utils import timezone

from stats.payment.utils import get_payment_stats_dict
from stats.models import GlobalStats, GroupStats, Definitions
from stats.tack.utils import get_tack_stats_dict
from stats.user.utils import get_user_stats_dict
from stats.payment.service import PaymentStats
from stats.user.service import UserStats
from stats.tack.service import TackStats
from group.models import Group
from tack.models import Tack
from user.models import User

logger = logging.getLogger('debug')
definitions = Definitions.objects.last()
active_user_timedelta_days = definitions.active_user_timedelta_days if definitions else 7


@shared_task
def migrate_avg_first_offer_time():
    class Epoch(django.db.models.expressions.Func):
        template = 'EXTRACT(epoch FROM %(expressions)s)::INTEGER'
        output_field = models.IntegerField()

    global_stats = GlobalStats.objects.all()
    global_stats.update(
        avg_first_offer_time_seconds=Epoch(F('avg_first_offer_time'))
    )

    group_stats = GroupStats.objects.all()
    group_stats.update(
        avg_first_offer_time_seconds=Epoch(F('avg_first_offer_time'))
    )


@shared_task
def collect_stats():
    """Main task for collecting statistics for grafana"""

    tack_stats = TackStats(
        created_tacks_last_hour=Tack.objects.filter(
            creation_time__gte=timezone.now() - timedelta(hours=1)
        ),
        accepted_tacks_last_hour=Tack.objects.filter(
            accepted_time__gte=timezone.now() - timedelta(hours=1)
        ),
        completed_tacks_last_hour=Tack.objects.filter(
            completion_time__gte=timezone.now() - timedelta(hours=1)
        ),
        active_users_last_week=User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=active_user_timedelta_days)
        ),
    )
    user_stats = UserStats()
    payment_stats = PaymentStats()

    start_time = time.time()
    global_tack_stats_dict = get_tack_stats_dict(tack_stats)
    global_user_stats_dict = get_user_stats_dict(user_stats)
    global_payment_stats_dict = get_payment_stats_dict(payment_stats)
    global_stats_dict = global_tack_stats_dict | global_user_stats_dict | global_payment_stats_dict
    logger.debug(f"{global_stats_dict = }")
    GlobalStats.objects.create(**global_stats_dict)
    logger.info(f"Global stats took ~ {round(time.time() - start_time, 2)} seconds")

    start_time = time.time()
    collected_group_for_stats = Group.objects.filter(collect_stats=True)
    group_stats_list = []
    for group in collected_group_for_stats:
        payment_stats = PaymentStats(group=group)
        group_tack_stats_dict = get_tack_stats_dict(tack_stats, group=group)
        group_user_stats_dict = get_user_stats_dict(user_stats, group=group)
        group_payment_stats_dict = get_payment_stats_dict(payment_stats, group=group)
        group_stats_dict = {"group": group} | group_tack_stats_dict | group_user_stats_dict | group_payment_stats_dict
        logger.debug(f"{group_stats_dict = }")
        group_stats_list.append(GroupStats(**group_stats_dict))
    GroupStats.objects.bulk_create(group_stats_list)
    logger.info(f"Group stats took ~ {round(time.time() - start_time, 2)} seconds")

    logger.info("Stats collection finished")
