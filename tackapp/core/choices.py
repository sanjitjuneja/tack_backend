from django.db import models


class SMSType(models.TextChoices):
    """Choices for sms type"""
    recovery = "R", "Recovery"
    signup = "S", "Signup"
