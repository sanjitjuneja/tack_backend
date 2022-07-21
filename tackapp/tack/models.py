from django.db import models
from django.core.validators import (
    DecimalValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db.models import UniqueConstraint

from core.choices import TackStatus, OfferType
from user.models import User


class Tack(models.Model):
    tacker = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, related_name="tack_tacker"
    )
    runner = models.ForeignKey(
        "user.User", on_delete=models.DO_NOTHING, related_name="tack_runner", null=True, blank=True
    )
    title = models.CharField(max_length=64)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=(
            DecimalValidator(8, 2),
            MinValueValidator(0),
            MaxValueValidator(999_999.99),
        ),
    )
    description = models.CharField(max_length=512)
    creation_time = models.DateTimeField(auto_now_add=True)
    expiration_time = models.DateTimeField()
    allow_counter_offer = models.BooleanField()
    status = models.CharField(
        max_length=16, choices=TackStatus.choices, default=TackStatus.created
    )
    # setting after Runner completed the Tack
    completion_message = models.CharField(max_length=256, null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    # setting before Tack creating (for the info)
    estimation_time_seconds = models.PositiveIntegerField(default=0)

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


class Offer(models.Model):
    tack = models.ForeignKey("tack.Tack", on_delete=models.CASCADE)
    runner = models.ForeignKey("user.User", on_delete=models.CASCADE)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=(
            DecimalValidator(8, 2),
            MinValueValidator(0),
            MaxValueValidator(999_999.99),
        ),
        null=True
    )
    offer_type = models.CharField(max_length=13, choices=OfferType.choices, default=OfferType.offer)
    is_accepted = models.BooleanField(default=False)
    creation_time = models.DateTimeField(auto_now=True)
    lifetime_seconds = models.PositiveIntegerField(default=900)

    class Meta:
        db_table = "offers"
        verbose_name = "Offer"
        verbose_name_plural = "Offers"

        constraints = [
            UniqueConstraint(fields=['tack', 'runner'], name='unique_runner_for_tack')
        ]
