import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tackapp.settings")
app = Celery("tackapp")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
