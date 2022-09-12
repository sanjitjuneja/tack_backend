from django.apps import AppConfig


class GroupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tack_group"

    def ready(self):
        from . import signals
