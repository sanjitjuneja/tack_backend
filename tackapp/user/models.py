from datetime import datetime
from uuid import uuid4

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from core.validators import username_validator
from review.models import Review


def upload_path_user_avs(instance, filename: str):
    extension = filename.split(".")[-1]
    today = datetime.today()
    year, month = today.year, today.month
    return f"profiles/{year}/{month}/{uuid4()}.{extension}"


class LowercaseEmailField(models.EmailField):
    """
    Override EmailField to convert emails to lowercase before saving.
    """
    def to_python(self, value):
        """
        Convert email to lowercase.
        """
        value = super(LowercaseEmailField, self).to_python(value)
        # Value can be None so check that it's a string before lowercasing.
        if isinstance(value, str):
            return value.lower()
        return value


class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, phone_number, password=None, **extra_fields):
        """Create and save a User with the given phone and password."""
        if not phone_number:
            raise ValueError('The given phone_number must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Create and save a SuperUser with the given phone and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=150, validators=(username_validator,), default="")
    password = models.CharField(max_length=128)
    profile_picture = models.ImageField(
        null=True, blank=True, upload_to=upload_path_user_avs
    )
    first_name = models.CharField(max_length=150, default="")
    last_name = models.CharField(max_length=150, default="")
    phone_number = PhoneNumberField(unique=True)
    birthday = models.DateField(null=True, blank=True)
    active_group = models.ForeignKey("group.Group", on_delete=models.SET_NULL, null=True, blank=True, default=None)
    tacks_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5)
    tacks_amount = models.PositiveIntegerField(default=0)
    email = LowercaseEmailField(unique=True, null=True, default=None)
    allowed_to_withdraw = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def get_contacts(self):
        return {"phone_number": self.phone_number, "email": self.email}

    def __str__(self):
        user = User.objects.get(id=self.id)
        return f"{user.last_name} {user.first_name} {user.phone_number}"

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
