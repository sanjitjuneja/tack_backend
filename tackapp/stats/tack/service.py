from django.db.models import Count, Avg, FloatField, ExpressionWrapper, QuerySet
from django.db.models.functions import Coalesce

from group.models import Group
from stats.utils import _setup_filters
from tack.models import Tack
from user.models import User


class TackStats:
    def __init__(
        self,
        created_tacks_last_hour: QuerySet[Tack],
        accepted_tacks_last_hour: QuerySet[Tack],
        completed_tacks_last_hour: QuerySet[Tack],
        active_users_last_week: QuerySet[User],
    ):
        self.created_tacks_last_hour = created_tacks_last_hour
        self.accepted_tacks_last_hour = accepted_tacks_last_hour
        self.completed_tacks_last_hour = completed_tacks_last_hour
        self.active_users_last_week = active_users_last_week

    def get_num_tacks_created_last_hour(self, group: Group = None):
        filters = _setup_filters(group=group)
        return self.created_tacks_last_hour.filter(
            **filters
        ).count()

    def get_num_tacks_accepted_last_hour(self, group: Group = None):
        filters = _setup_filters(group=group)
        return self.accepted_tacks_last_hour.filter(
            **filters
        ).count()

    def get_num_tacks_completed_last_hour(self, group: Group = None):
        filters = _setup_filters(group=group)
        return self.completed_tacks_last_hour.filter(
            **filters
        ).count()

    def get_num_tacks_created_by_tackers_last_hour(self, group: Group = None):
        filters = _setup_filters(group=group)
        tackers = self.active_users_last_week.filter(
            **filters
        ).annotate(
            tack_num=Count('tack_tacker')
        ).filter(
            tack_num__gte=1
        )
        return Tack.objects.filter(
            tacker__in=tackers,
            **filters
        ).count()

    def get_num_tacks_completed_by_runners_last_hour(self, group: Group = None):
        filters = _setup_filters(group=group)
        runners = self.active_users_last_week.filter(
            **filters
        ).annotate(
            tack_num=Count('tack_runner')
        ).filter(
            tack_num__gte=3
        )
        return Tack.objects.filter(
            runner__in=runners,
            **filters
        ).count()

    def get_avg_price_last_hour(self, group: Group = None):
        filters = _setup_filters(group=group)
        return self.created_tacks_last_hour.filter(
            **filters
        ).aggregate(
            avg_price=Avg('price')
        )["avg_price"] or 0

    def get_avg_tackers_time_estimation(self, group: Group = None):
        filters = _setup_filters(group=group)
        tackers = self.active_users_last_week.filter(
            **filters
        ).annotate(
            tack_num=Count('tack_tacker')
        ).filter(
            tack_num__gte=1
        )
        return self.created_tacks_last_hour.filter(
            tacker__in=tackers,
            **filters
        ).aggregate(
            avg_time_estimation_sec=Avg('time_estimation_seconds')
        )["avg_time_estimation_sec"] or 0

    def get_avg_acceptance_time(self, group: Group = None):
        filters = _setup_filters(group=group)
        return self.accepted_tacks_last_hour.filter(
            accepted_time__isnull=False,
            **filters
        ).aggregate(
            avg_accepted_time=Avg('accepted_time')
        )["avg_accepted_time"]

    def get_runner_tacker_ratio(self, group: Group = None):
        filters = _setup_filters(group=group)
        tackers = self.active_users_last_week.filter(
            **filters
        ).annotate(
            tack_num=Count('tack_tacker')
        ).filter(
            tack_num__gte=1
        )
        runners = self.active_users_last_week.filter(
            **filters
        ).annotate(
            tack_num=Count('tack_runner')
        ).filter(
            tack_num__gte=3
        )
        return len(runners) / len(tackers) if len(tackers) else len(runners)

    def get_avg_num_offers_before_accept(self, group: Group = None):
        filters = _setup_filters(group=group)
        return self.accepted_tacks_last_hour.filter(
            **filters
        ).annotate(
            num_offers=Count("offer")
        ).aggregate(
            avg_offer_num_before_accept=ExpressionWrapper(
                Coalesce(Avg("num_offers"), 0),
                output_field=FloatField()
            )
        )["avg_offer_num_before_accept"]

    def get_num_allowed_counteroffers(self, group: Group = None):
        filters = _setup_filters(group=group)
        return self.created_tacks_last_hour.filter(
            allow_counter_offer=True,
            **filters
        ).count()
