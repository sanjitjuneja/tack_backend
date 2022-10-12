from group.models import Group
from stats.tack.service import TackStats
from stats.utils import _setup_filters


def get_tack_stats_dict(tack_stats: TackStats, *, group: Group = None):
    filters = _setup_filters(group=group)
    return {
            "num_tacks_created_last_hour": tack_stats.get_num_tacks_created_last_hour(**filters),
            "num_tacks_accepted_last_hour": tack_stats.get_num_tacks_accepted_last_hour(**filters),
            "num_tacks_completed_last_hour": tack_stats.get_num_tacks_completed_last_hour(**filters),
            "num_tacks_created_by_tackers_last_hour": tack_stats.get_num_tacks_created_by_tackers_last_hour(**filters),
            "num_tacks_completed_by_runners_last_hour": tack_stats.get_num_tacks_completed_by_runners_last_hour(**filters),
            "avg_price_last_hour": tack_stats.get_avg_price_last_hour(**filters),
            "avg_tackers_time_estimation": tack_stats.get_avg_tackers_time_estimation(**filters),
            "avg_first_offer_time": tack_stats.get_avg_first_offer_time(**filters),
            "runner_tacker_ratio": tack_stats.get_runner_tacker_ratio(**filters),
            "avg_num_offers_before_accept": tack_stats.get_avg_num_offers_before_accept(**filters),
            "num_allowed_counteroffers": tack_stats.get_num_allowed_counteroffers(**filters),
        }
