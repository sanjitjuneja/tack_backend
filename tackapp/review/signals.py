from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Review
from payment.services import send_payment_to_runner
from review.services import get_reviews_by_user


@receiver(signal=post_save, sender=Review)
def send_payment_on_review(instance: Review, created: bool, *args, **kwargs):
    if created and instance.user == instance.tack.tacker:
        send_payment_to_runner(instance.tack)


@receiver(signal=post_save, sender=Review)
def change_tacks_rating_on_review_save(instance: Review, created: bool, *args, **kwargs):
    if created:
        reviewed_user = instance.tack.runner \
            if instance.user == instance.tack.tacker \
            else instance.tack.tacker
        reviews_qs = get_reviews_by_user(reviewed_user)
        reviewed_user.tacks_rating = reviews_qs.aggregate(Avg('rating'))
        reviewed_user.save()
