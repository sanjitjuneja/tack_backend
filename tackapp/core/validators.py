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


class CustomPasswordValidator:

    def __init__(self, min_length=1):
        self.min_length = min_length

    def validate(self, password, user=None):
        if not 8 <= len(password) <= 16:
            raise ValidationError(
                _('Password length must be in length 8 to 16 characters'))
        if not any(char.isdigit() for char in password):
            raise ValidationError(_('Password must contain at least %(min_length)d digit.') % {'min_length': self.min_length})
        if not any(char.isalpha() for char in password):
            raise ValidationError(_('Password must contain at least %(min_length)d letter.') % {'min_length': self.min_length})

    def get_help_text(self):
        return ""

# def price_validator(value) -> bool:
#     print(value)
#     print(type(value))
#     return True
