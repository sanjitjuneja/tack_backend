from django.db import models
from django.templatetags.static import static

from tackapp.settings import S3_BUCKET_TACKAPPSTORAGE, S3_BUCKET_CARDS, S3_BUCKET_BANKS

images_dict = {
    "visa": f"{S3_BUCKET_TACKAPPSTORAGE}{S3_BUCKET_CARDS}/visa.png",
    "mastercard": f"{S3_BUCKET_TACKAPPSTORAGE}{S3_BUCKET_CARDS}/mastercard.png",
    "discover": f"{S3_BUCKET_TACKAPPSTORAGE}{S3_BUCKET_CARDS}/discover.png",
    "american-express": f"{S3_BUCKET_TACKAPPSTORAGE}{S3_BUCKET_CARDS}/american-express.png",
    # "CHASE": f"{S3_BUCKET_TACKAPPSTORAGE}{S3_BUCKET_BANKS}/chase.png",
}


class SMSType(models.TextChoices):
    """Choices for sms type"""

    RECOVERY = "R", "Recovery"
    SIGNUP = "S", "Signup"


class TackStatus(models.TextChoices):
    """Choice for Tack status"""

    CREATED = "created", "Created"  # Tack created by Tacker
    ACTIVE = "active", "Active"  # Someone created an offer to the Tack
    ACCEPTED = "accepted", "Accepted"  # Offer accepted, waiting for Runner to start
    IN_PROGRESS = "in_progress", "In progress"  # Runner started the Tack, Tack is in progress
    WAITING_REVIEW = "waiting_review", "Waiting Review"  # Tack is completed by Runner
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


class PaymentType(models.TextChoices):
    """Choices for check Payment type"""

    BANK = "bank", "Bank"
    CARD = "card", "Card"
