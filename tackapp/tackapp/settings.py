"""
Django settings for tackapp project.

Generated by 'django-admin startproject' using Django 4.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import json
import logging
import os
import re
from datetime import timedelta
from pathlib import Path
import environ
import django
import stripe
from django.utils.encoding import force_str
from firebase_admin import initialize_app

from core.logs_formatter import CustomJsonFormatter
from tackapp.services_env import read_secrets
from aws.secretmanager import receive_setting_secrets
from aws.ssm import receive_setting_parameters
django.utils.encoding.force_text = force_str


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json_formatter': {
            '()': CustomJsonFormatter
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'debug_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'payment_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/payments.log',
            'formatter': 'json_formatter'
        },
        'sql_measurement': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/sql_queues.log',
            'formatter': 'json_formatter'
        }
    },
    'loggers': {
        'django': {
            'handlers': ('console',),
            'propagate': True,
        },
        'payments': {
            'handlers': ('payment_file', 'console',),
            'level': 'INFO'
        },
        'tackapp.consumers': {
            'handlers': ('console',),
            'level': 'INFO'
        },
        'tackapp.channels_middleware': {
            'handlers': ('console',),
            'level': 'ERROR'
        },
        'sql_time_measurement': {
            'handlers': ('sql_measurement',),
            'level': 'INFO'
        }
    }
}
os.makedirs(os.path.dirname(LOGGING['handlers']['payment_file']['filename']), exist_ok=True)
logger = logging.getLogger('django')


app = os.getenv("APP")
logger.info(f"{app = }")
if app == "dev":
    temp_env = environ.Env(DEBUG=(bool, False))
    temp_env.read_env(os.path.join(BASE_DIR, "dev.env"))
    env = receive_setting_secrets(
        temp_env("AWS_ACCESS_KEY_ID"),
        temp_env("AWS_SECRET_ACCESS_KEY"),
        temp_env("AWS_REGION"),
        "dev/tackapp/django"
    )
    DEBUG = env.get("DEBUG")
elif app == "local":
    env = environ.Env(DEBUG=(bool, True))
    env.read_env(os.path.join(BASE_DIR, "local.env"))
    DEBUG = read_secrets(app, env, "DEBUG")
else:
    temp_env = environ.Env(DEBUG=(bool, False))
    temp_env.read_env(os.path.join(BASE_DIR, "prod.env"))

    env = receive_setting_secrets(
        temp_env("AWS_ACCESS_KEY_ID"),
        temp_env("AWS_SECRET_ACCESS_KEY"),
        temp_env("AWS_REGION"),
        "prod/tackapp/"
    )
    DEBUG = True if read_secrets(app, env, "DEBUG") == "True" else False

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
AWS_ACCESS_KEY_ID = read_secrets(app, env, "AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = read_secrets(app, env, "AWS_SECRET_ACCESS_KEY")
AWS_REGION = read_secrets(app, env, "AWS_REGION")
ALLOWED_HOSTS = read_secrets(app, env, "ALLOWED_HOSTS").split(",")


SECRET_KEY = read_secrets(app, env, "DJANGO_SECRET_KEY")


logger.info(f"{DEBUG = }")

logger.info(f"{ALLOWED_HOSTS = }")
if DEBUG:
    import socket  # only if you haven't already imported this
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]
    INTERNAL_IPS += ["172.25.0.5"]
    logger.info(f"{INTERNAL_IPS = }")

# Application definition

INSTALLED_APPS = [
    "debug_toolbar",
    # "jet.dashboard",
    # "jet",
    "custom_admin.apps.CustomAdminConfig",
    # "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "user.apps.UserConfig",
    "djstripe",
    "tack.apps.TackConfig",
    "review.apps.ReviewConfig",
    "group.apps.GroupConfig",
    "socials.apps.SocialsConfig",
    "payment.apps.PaymentConfig",
    "dwolla_service.apps.DwollaServiceConfig",
    "stats.apps.StatsConfig",
    "drf_spectacular",
    "rest_framework",
    "sslserver",
    "phonenumber_field",
    "django_filters",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "storages",
    "fcm_django",
    "django_celery_beat",
    "advanced_filters"
]


MIDDLEWARE = [
    # "tackapp.middleware.RequestTimeMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tackapp.urls"

SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_URL_NAMESPACE = "social"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# WSGI_APPLICATION = "tackapp.wsgi.application"
ASGI_APPLICATION = "tackapp.asgi.application"


CHANNEL_LAYERS_HOSTS = read_secrets(app, env, "CHANNEL_LAYERS_HOSTS").split(",")
logger.info(f"{CHANNEL_LAYERS_HOSTS = }")
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [CHANNEL_LAYERS_HOSTS],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "tackapp",
        "NAME": read_secrets(app, env, "POSTGRES_DB"),
        "USER": read_secrets(app, env, "POSTGRES_USER"),
        "PASSWORD": read_secrets(app, env, "POSTGRES_PASSWORD"),
        "HOST": read_secrets(app, env, "POSTGRES_HOST"),
        "PORT": read_secrets(app, env, "POSTGRES_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "core.validators.CustomPasswordValidator"
    }
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
AWS_STORAGE_BUCKET_NAME = read_secrets(app, env, 'AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_FILE_OVERWRITE = True if read_secrets(app, env, 'AWS_S3_FILE_OVERWRITE') == "True" else False
AWS_DEFAULT_ACL = read_secrets(app, env, 'AWS_DEFAULT_ACL')
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_QUERYSTRING_AUTH = True if read_secrets(app, env, 'AWS_QUERYSTRING_AUTH') == "True" else False
AWS_HEADERS = {
    "Access-Control-Allow-On"
}

STATIC_LOCATION = read_secrets(app, env, 'STATIC_LOCATION')
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'
STATICFILES_STORAGE = 'tackapp.storage_backends.StaticStorage'

PUBLIC_MEDIA_LOCATION = read_secrets(app, env, 'PUBLIC_MEDIA_LOCATION')
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"
DEFAULT_FILE_STORAGE = 'tackapp.storage_backends.PublicMediaStorage'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'staticfiles'),)

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "user.User"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.LastObjectPagination',
    'PAGE_SIZE': 10,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Tackapp API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': "/api/v1",
    'COMPONENT_SPLIT_REQUEST': True
}

# Twilio
TWILIO_ACCOUNT_SID = read_secrets(app, env, "TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = read_secrets(app, env, "TWILIO_AUTH_TOKEN")
MESSAGING_SERVICE_SID = read_secrets(app, env, "MESSAGING_SERVICE_SID")


CELERY_BROKER_URL = read_secrets(app, env, "CELERY_BROKER")


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=9),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=10),
}

CSRF_TRUSTED_ORIGINS = read_secrets(app, env, "CSRF_TRUSTED_ORIGINS").split(",")

STRIPE_PUBLISHABLE_KEY = read_secrets(app, env, "STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = read_secrets(app, env, "STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# STRIPE_LIVE_SECRET_KEY = os.environ.get("STRIPE_LIVE_SECRET_KEY", "<your secret key>")
STRIPE_TEST_SECRET_KEY = read_secrets(app, env, "STRIPE_SECRET_KEY")
STRIPE_LIVE_MODE = False  # Change to True in production
DJSTRIPE_USE_NATIVE_JSONFIELD = True  # We recommend setting to True for new installations
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
# DJSTRIPE_WEBHOOK_VALIDATION = 'retrieve_event'
DJSTRIPE_WEBHOOK_SECRET = read_secrets(app, env, "STRIPE_WEBHOOK_SECRET")


DWOLLA_APP_KEY = read_secrets(app, env, 'DWOLLA_APP_KEY')
DWOLLA_APP_SECRET = read_secrets(app, env, 'DWOLLA_APP_SECRET')
DWOLLA_MAIN_FUNDING_SOURCE = read_secrets(app, env, 'DWOLLA_MAIN_FUNDING_SOURCE')
DWOLLA_WEBHOOK_SECRET = read_secrets(app, env, 'DWOLLA_WEBHOOK_SECRET')
PLAID_CLIENT_ID = read_secrets(app, env, "PLAID_CLIENT_ID")
PLAID_CLIENT_SECRET = read_secrets(app, env, "PLAID_CLIENT_SECRET")


FIREBASE_CONFIG = {
    "type": read_secrets(app, env, "FIREBASE_TYPE"),
    "project_id": read_secrets(app, env, "FIREBASE_PROJECT_ID"),
    "private_key_id": read_secrets(app, env, "FIREBASE_PRIVATE_KEY_ID"),
    "private_key": re.sub(r"\\n", r"\n", read_secrets(app, env, "FIREBASE_PRIVATE_KEY")),
    "client_email": read_secrets(app, env, "FIREBASE_CLIENT_EMAIL"),
    "client_id": read_secrets(app, env, "FIREBASE_CLIENT_ID"),
    "auth_uri": read_secrets(app, env, "FIREBASE_AUTH_URI"),
    "token_uri": read_secrets(app, env, "FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": read_secrets(app, env, "FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": read_secrets(app, env, "FIREBASE_CLIENT_X509_CERT_URL"),
}

with open(os.path.split(os.path.dirname(__file__))[0] + "/firebase_config.json", "w") as firebase_config_file:
    json.dump(FIREBASE_CONFIG, firebase_config_file, indent=2)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = read_secrets(app, env, "GOOGLE_APPLICATION_CREDENTIALS")
FIREBASE_APP = initialize_app()

FCM_DJANGO_SETTINGS = {
     # default: _('FCM Django')
    "APP_VERBOSE_NAME": "FCM Devices",
     # true if you want to have only one active device per registered user at a time
     # default: False
    "ONE_DEVICE_PER_USER": False,
     # devices to which notifications cannot be sent,
     # are deleted upon receiving error response from FCM
     # default: False
    "DELETE_INACTIVE_DEVICES": False,
}

S3_BUCKET_TACKAPPSTORAGE = AWS_S3_CUSTOM_DOMAIN

S3_BUCKET_CARDS = "payment_methods/cards"
S3_BUCKET_BANKS = "payment_methods/banks"
S3_BUCKET_DIGITAL_WALLETS = "payment_methods/digital_wallets"


# X_FRAME_OPTIONS = 'SAMEORIGIN'
