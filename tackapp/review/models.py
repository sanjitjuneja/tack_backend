from django.db import models
from core.choices import ReviewRating


class Review(models.Model):
    user = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, related_name="review_user"
    )
    tack = models.ForeignKey(
        "tack.Tack", on_delete=models.CASCADE, related_name="review_tack"
    )
    rating = models.PositiveSmallIntegerField(choices=ReviewRating.choices)
    description = models.CharField(max_length=256)

    def __str__(self):
        return f"{self.description[:20]}, {self.rating}, {self.user}"

    class Meta:
        db_table = "reviews"
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
