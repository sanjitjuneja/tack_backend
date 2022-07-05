from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from .validators import password_validator


class User(AbstractUser):
    password = models.CharField(max_length=128, validators=(password_validator,))
    profile_picture = models.ImageField(
        null=True, blank=True, upload_to="static/media/profile_pictures/"
    )
    phone_number = PhoneNumberField(null=True, blank=True, unique=True)
    birthday = models.DateField(null=True)

    def __str__(self):
        return f"{self.username}, {self.last_name} {self.first_name}"

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
