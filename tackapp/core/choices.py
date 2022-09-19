from enum import Enum

from django.db import models

from tackapp.settings import S3_BUCKET_CARDS, S3_BUCKET_BANKS, MEDIA_URL

images_dict = {
    "visa": f"{MEDIA_URL}{S3_BUCKET_CARDS}/visa.png",
    "mastercard": f"{MEDIA_URL}{S3_BUCKET_CARDS}/mastercard.png",
    "discover": f"{MEDIA_URL}{S3_BUCKET_CARDS}/discover.png",
    "american-express": f"{MEDIA_URL}{S3_BUCKET_CARDS}/american-express.png",
    # "CHASE": f"{STATIC_URL}{S3_BUCKET_BANKS}/chase.png",
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


class PaymentService(models.TextChoices):
    """Choices for Payment services (Stripe, Dwolla)"""

    STRIPE = "stripe", "Stripe"
    DWOLLA = "dwolla", "Dwolla"


class PaymentAction(models.TextChoices):
    """Choices for Payment Action"""

    DEPOSIT = "deposit", "Deposit"
    WITHDRAW = "withdraw", "Withdraw"


class OfferStatus(models.TextChoices):
    """Choices for Offer status"""

    CREATED = "created", "Created"
    ACCEPTED = "accepted", "Accepted"
    IN_PROGRESS = "in_progress", "In progress"
    FINISHED = "finished", "Finished"
    DELETED = "deleted", "Deleted"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class NotificationType(Enum):
    TACK_CREATED = "tack_created"
    TACK_ACCEPTED = "tack_accepted"
    TACK_IN_PROGRESS = "tack_in_progress"
    TACK_WAITING_REVIEW = "tack_waiting_review"
    TACK_FINISHED = "tack_finished"

    TACK_EXPIRING = "tack_expiring"
    TACK_INACTIVE = "tack_inactive"
    TACK_CANCELLED = "tack_canceled"

    OFFER_RECEIVED = "offer_received"
    COUNTEROFFER_RECEIVED = "counteroffer_received"
    OFFER_ACCEPTED = "offer_accepted"
    RUNNER_FINISHED = "runner_finished"
    OFFER_EXPIRED = "offer_expired"


