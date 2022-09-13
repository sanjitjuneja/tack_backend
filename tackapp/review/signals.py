import logging

from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.choices import TackStatus
from .models import Review
from payment.services import send_payment_to_runner
from review.services import get_reviews_by_user, change_tacks_rating_on_review_save


@receiver(signal=post_save, sender=Review)
def change_tack_status_on_review_save(instance: Review, created: bool, *args, **kwargs):
    if created:
        # send_payment_to_runner(instance.tack)
        change_tacks_rating_on_review_save(review=instance)

#
# @receiver(signal=post_save, sender=Review)
# def change_tack_status_on_review_save(instance: Review, created: bool, *args, **kwargs):
#     if created:
#         instance.tack.change_status(TackStatus.FINISHED)
