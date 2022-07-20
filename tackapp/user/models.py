from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


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
    username = models.CharField(max_length=150, null=True, blank=True)
    password = models.CharField(max_length=128)
    profile_picture = models.ImageField(
        null=True, blank=True, upload_to="static/media/profile_pictures/"
    )
    first_name = models.CharField(max_length=150, default="")
    last_name = models.CharField(max_length=150, default="")
    phone_number = PhoneNumberField(unique=True)
    birthday = models.DateField(null=True)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tacks_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    tacks_amount = models.PositiveIntegerField(default=0)

    objects = CustomUserManager()

    # @property
    # def tacks_rating(self):
    #     return Review.objects.filter(tacker=self.pk).aggregate(Avg("rating"))[
    #         "rating__avg"
    #     ]

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
