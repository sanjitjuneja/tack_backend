import logging

from django.db.models import Q, Avg

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


def change_tacks_rating_on_review_save(review: Review):
    reviewed_user = review.tack.runner \
        if review.user == review.tack.tacker \
        else review.tack.tacker
    reviews_qs = get_reviews_by_user(reviewed_user)
    rating = reviews_qs.aggregate(Avg('rating'))["rating__avg"]
    reviewed_user.tacks_rating = rating
    reviewed_user.save()


