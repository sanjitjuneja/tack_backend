from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def password_validator(value: str) -> bool:
    errors = {}
    if not 8 <= len(value) <= 16:
        errors["length"] = "Password must be in range 8-16 characters"
    if not any(char.isdigit() for char in value):
        errors["digits"] = "Password must contain at least 1 Digit"
    if not any(char.isupper() for char in value):
        errors["uppercase"] = "Password must contain at least 1 Capital Letter"
    if errors:
        raise ValidationError(
            [ValidationError(_(message), code) for code, message in errors.items()]
        )
    return True
