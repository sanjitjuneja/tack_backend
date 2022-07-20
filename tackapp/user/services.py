from django.db.models import Q

from review.models import Review


def get_reviews_by_user(user):
    # Reviews where User.id is Tack.tacker or Tack.runner but not Review.user
    qs = Review.objects.filter(
                (Q(tack__tacker=user) | Q(tack__runner=user)) &
                ~Q(user=user)
            ).select_related("tack")
    return qs


def get_reviews_as_reviewer_by_user(user):
    qs = Review.objects.filter(user=user).select_related("tack")
    return qs
