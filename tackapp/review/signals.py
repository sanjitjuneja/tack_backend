from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Review
from review.services import change_tacks_rating_on_review_save


@receiver(signal=post_save, sender=Review)
def change_tack_status_on_review_save(instance: Review, created: bool, *args, **kwargs):
    if created:
        change_tacks_rating_on_review_save(review=instance)
