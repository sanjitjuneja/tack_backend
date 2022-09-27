from django.db import models
from django.db.models import UniqueConstraint

from core.abstract_models import CoreModel
from core.choices import ReviewRating


class Review(CoreModel):
    user = models.ForeignKey(
        "user.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="review_user"
    )
    tack = models.ForeignKey(
        "tack.Tack", on_delete=models.CASCADE, related_name="review_tack"
    )
    rating = models.PositiveSmallIntegerField(choices=ReviewRating.choices)
    description = models.CharField(max_length=256, null=True, blank=True, default=None)

    def __str__(self):
        return f"Review {self.id}: {self.user} {self.rating} on {self.tack}"

    class Meta:
        db_table = "reviews"
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        constraints = [
            UniqueConstraint(fields=['user', 'tack'], name='unique_user_for_tack')
        ]
