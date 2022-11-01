from django.db import models, transaction
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db.models import UniqueConstraint, Q

from core.abstract_models import CoreModel
from core.choices import TackStatus, OfferType, TackType, OfferStatus
from payment.models import BankAccount
from user.models import User


class Tack(CoreModel):
    tacker = models.ForeignKey(
        "user.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="tack_tacker"
    )
    runner = models.ForeignKey(
        "user.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="tack_runner",
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
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE
    )
    description = models.CharField(max_length=512)
    allow_counter_offer = models.BooleanField()
    status = models.CharField(
        max_length=16, choices=TackStatus.choices, default=TackStatus.CREATED
    )
    is_paid = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    estimation_time_seconds = models.PositiveIntegerField(null=True, blank=True, default=None)
    auto_accept = models.BooleanField(default=False)
    # setting after Tacker accepts Runner's Offer
    accepted_time = models.DateTimeField(null=True, blank=True)
    accepted_offer = models.ForeignKey("tack.Offer", on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name="tack_accepted_offer")
    # setting after Runner started completing Tack
    start_completion_time = models.DateTimeField(null=True, blank=True, default=None)
    # setting after Runner completed Tack
    completion_message = models.CharField(max_length=256, null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        super().delete()

    def cancel(self):
        if self.is_canceled:
            return
        with transaction.atomic():
            self.is_active = False
            self.is_canceled = True
            if self.accepted_offer:
                self.accepted_offer.status = OfferStatus.CANCELLED
                self.accepted_offer.is_active = False
                ba = BankAccount.objects.get(user=self.tacker)
                ba.usd_balance += self.price
                ba.save()
                self.accepted_offer.save()
            self.save()

    def change_status(self, status: TackStatus):
        self.status = status
        self.save()

    def is_participant(self, user: User):
        return not (self.tacker != user and self.runner != user)

    def __str__(self):
        return f"{self.pk}: {self.title}"

    class Meta:
        db_table = "tacks"
        verbose_name = "Tack"
        verbose_name_plural = "Tacks"


class Offer(CoreModel):
    tack = models.ForeignKey("tack.Tack", on_delete=models.CASCADE)
    runner = models.ForeignKey("user.User", null=True, blank=True, on_delete=models.SET_NULL)
    price = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(999_999_99),
        ),
        null=True,
        blank=True
    )
    offer_type = models.CharField(max_length=13, choices=OfferType.choices, default=OfferType.OFFER)
    lifetime_seconds = models.PositiveIntegerField(default=900)
    status = models.CharField(max_length=12, choices=OfferStatus.choices, default=OfferStatus.CREATED)

    def __str__(self):
        return f"{self.id}: {self.tack.title}"

    def set_expired_status(self):
        self.status = OfferStatus.EXPIRED
        self.is_active = False
        self.save()

    def delete(self, using=None, keep_parents=False):
        self.status = OfferStatus.DELETED
        super().delete()

    class Meta:
        db_table = "offers"
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        constraints = [
            UniqueConstraint(
                fields=('tack', 'runner'),
                condition=Q(is_active=True),
                name='unique_runner_for_tack'
            )
        ]


class PopularTack(models.Model):
    tacker = models.ForeignKey(
        "user.User", null=True, blank=True, on_delete=models.SET_NULL, default=None
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
    auto_accept = models.BooleanField(default=False)
    group = models.ForeignKey("group.Group", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=512)
    allow_counter_offer = models.BooleanField()
    estimation_time_seconds = models.PositiveIntegerField(null=True, blank=True, default=None)

    class Meta:
        db_table = "popular_tacks"
        verbose_name = "Popular Tack"
        verbose_name_plural = "Popular Tacks"
