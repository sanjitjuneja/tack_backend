from django.db import models


class SMSType(models.TextChoices):
    """Choices for sms type"""

    recovery = "R", "Recovery"
    signup = "S", "Signup"


class TackStatus(models.TextChoices):
    """Choice for Tack status"""

    created = "created", "Just created"  # Tack created by Tacker
    active = "active", "Tack have active Offers"  # Someone created an offer to the Tack
    accepted = "accepted", "Offer accepted"  # Offer accepted, waiting for Runner to start
    in_progress = "in_progress", "In progress"  # Runner started the Tack, Tack is in progress
    waiting_review = "waiting_review", "Waiting for Review"  # Tack is completed by Runner
    finished = "finished", "Finished"  # Tack is fully completed either with Review or not


class TackType(models.TextChoices):
    """Tack Type"""
    groups = "groups", "Groups type"
    friends = "friends", "Friends type",
    public = "public", "Public (Anonymous)"


class OfferType(models.TextChoices):
    """Choice for Offer type"""

    offer = "offer", "Offer"
    counter_offer = "counter_offer", "Counter Offer"


class ReviewRating(models.IntegerChoices):
    """Choices for Review rating"""

    rating_1 = 1, "1 Star"
    rating_2 = 2, "2 Stars"
    rating_3 = 3, "3 Stars"
    rating_4 = 4, "4 Stars"
    rating_5 = 5, "5 Stars"


class TackTimeType(models.TextChoices):
    """Choices for Tack time type"""

    minutes = "minutes", "Minutes"
    hours = "hours", "Hours"
