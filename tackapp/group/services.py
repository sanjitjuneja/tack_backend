from group.models import Group, GroupTacks
from django.db.models import Subquery
from core.choices import TackStatus
from tack.models import Tack


def get_tacks_by_group(group: Group):
    """Retrieve all tacks in active statuses that attached to the Group"""

    active_statuses = (TackStatus.created, TackStatus.active)
    qs = Tack.objects.filter(
        id__in=Subquery(
            GroupTacks.objects.filter(
                group=group,
                tack__status__in=active_statuses
            ).select_related(
                "tack"
            ).values_list(
                "tack", flat=True)))
    return qs
