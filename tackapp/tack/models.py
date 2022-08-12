from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db.models import UniqueConstraint

from core.abstract_models import CoreModel
from core.choices import TackStatus, OfferType, TackType
from user.models import User


class Tack(CoreModel):
    tacker = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, related_name="tack_tacker"
    )
    runner = models.ForeignKey(
        "user.User", on_delete=models.DO_NOTHING, related_name="tack_runner", null=True, blank=True
    )
    title = models.CharField(max_length=64)
    type = models.CharField(
        max_length=7, choices=TackType.choices, default=TackType.GROUPS
    )
    price = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(999_999_99),
        ),
    )
    group = models.ForeignKey("group.Group", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=512)
    allow_counter_offer = models.BooleanField()
    status = models.CharField(
        max_length=16, choices=TackStatus.choices, default=TackStatus.CREATED
    )
    is_paid = models.BooleanField(default=False)
    estimation_time_seconds = models.PositiveIntegerField(null=True, blank=True, default=None)
    # setting after Tacker accepts Runner's Offer
    accepted_time = models.DateTimeField(null=True, blank=True)
    accepted_offer = models.ForeignKey("tack.Offer", on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name="tack_accepted_offer")
    # setting after Runner completed the Tack
    completion_message = models.CharField(max_length=256, null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)

    def change_status(self, status: str):
        self.status = status
        self.save()

    def is_participant(self, user: User):
        return not (self.tacker != user and self.runner != user)

    # payment_status
    # tacker rating
    # finished by user or by celery task
    # runner rating

    def __str__(self):
        return f"{self.pk}: {self.title}"

    class Meta:
        db_table = "tacks"
        verbose_name = "Tack"
        verbose_name_plural = "Tacks"


class Offer(CoreModel):
    tack = models.ForeignKey("tack.Tack", on_delete=models.CASCADE)
    runner = models.ForeignKey("user.User", on_delete=models.CASCADE)
    price = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(999_999_99),
        ),
        null=True,
        blank=True
    )
    offer_type = models.CharField(max_length=13, choices=OfferType.choices, default=OfferType.OFFER)
    is_accepted = models.BooleanField(default=False)
    lifetime_seconds = models.PositiveIntegerField(default=900)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "offers"
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        constraints = [
            UniqueConstraint(fields=('tack', 'runner'), name='unique_runner_for_tack')
        ]


class PopularTack(models.Model):
    tacker = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, null=True, blank=True, default=None
    )
    title = models.CharField(max_length=64)
    type = models.CharField(
        max_length=7, choices=TackType.choices, default=TackType.GROUPS
    )
    price = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(999_999_99),
        ),
    )
    group = models.ForeignKey("group.Group", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=512)
    allow_counter_offer = models.BooleanField()
    estimation_time_seconds = models.PositiveIntegerField(null=True, blank=True, default=None)

    class Meta:
        db_table = "popular_tacks"
        verbose_name = "Popular Tack"
        verbose_name_plural = "Popular Tacks"
