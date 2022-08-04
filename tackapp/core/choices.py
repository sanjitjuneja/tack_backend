from django.db import models


class SMSType(models.TextChoices):
    """Choices for sms type"""

    RECOVERY = "R", "Recovery"
    SIGNUP = "S", "Signup"


class TackStatus(models.TextChoices):
    """Choice for Tack status"""

    CREATED = "created", "Just created"  # Tack created by Tacker
    ACTIVE = "active", "Tack have active Offers"  # Someone created an offer to the Tack
    ACCEPTED = "accepted", "Offer accepted"  # Offer accepted, waiting for Runner to start
    IN_PROGRESS = "in_progress", "In progress"  # Runner started the Tack, Tack is in progress
    WAITING_REVIEW = "waiting_review", "Waiting for Review"  # Tack is completed by Runner
    FINISHED = "finished", "Finished"  # Tack is fully completed either with Review or not


class TackType(models.TextChoices):
    """Tack Type"""

    GROUPS = "groups", "Groups type"
    FRIENDS = "friends", "Friends type",
    PUBLIC = "public", "Public (Anonymous)"


class OfferType(models.TextChoices):
    """Choice for Offer type"""

    OFFER = "offer", "Offer"
    COUNTER_OFFER = "counter_offer", "Counter Offer"


class ReviewRating(models.IntegerChoices):
    """Choices for Review rating"""

    RATING_1 = 1, "1 Star"
    RATING_2 = 2, "2 Stars"
    RATING_3 = 3, "3 Stars"
    RATING_4 = 4, "4 Stars"
    RATING_5 = 5, "5 Stars"


class TackTimeType(models.TextChoices):
    """Choices for Tack time type"""

    MINUTES = "minutes", "Minutes"
    HOURS = "hours", "Hours"
