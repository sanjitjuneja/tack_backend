"""
Django settings for tackapp project.

Generated by 'django-admin startproject' using Django 4.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import os
from datetime import timedelta
from pathlib import Path
import environ
import django
import stripe
from django.utils.encoding import force_str
django.utils.encoding.force_text = force_str


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

if os.getenv("app") == "dev":
    env = environ.Env(DEBUG=(bool, True))
    environ.Env.read_env(os.path.join(BASE_DIR, "dev.env"))
else:
    env = environ.Env(DEBUG=(bool, False))
    environ.Env.read_env(os.path.join(BASE_DIR, "prod.env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = [
    "tackapp.net",
    "127.0.0.1",
    "44.203.217.242",
    "localhost",
    "backend.tackapp.net",
    "172.31.8.161",
]

INTERNAL_IPS = [
    "127.0.0.1"
]
# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "user.apps.UserConfig",
    "tack.apps.TackConfig",
    "review.apps.ReviewConfig",
    "group.apps.GroupConfig",
    "socials.apps.SocialsConfig",
    "payment.apps.PaymentConfig",
    "dwolla_service.apps.DwollaServiceConfig",
    "drf_spectacular",
    "rest_framework",
    "debug_toolbar",
    # "social_django",
    "sslserver",
    "phonenumber_field",
    "django_filters",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "djstripe",
]


MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "social_django.middleware.SocialAuthExceptionMiddleware",
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
                # "social_django.context_processors.backends",
                # "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "tackapp.wsgi.application"
# ASGI_APPLICATION = 'tackapp.asgi.application'
# AUTHENTICATION_BACKENDS = (
#     # "social_core.backends.google.GoogleOAuth2",
#     # "social_core.backends.facebook.FacebookOAuth2",
#     "django.contrib.auth.backends.ModelBackend",
# )

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
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


if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
else:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = "static/"

MEDIA_URL = 'media/'  # 'http://myhost:port/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "user.User"
# SOCIAL_AUTH_USER_MODEL = "user.User"

# LOGIN_REDIRECT_URL = "api/v1/accounts/profile/"
# LOGIN_URL = "api/v1/accounts/login/"
# LOGOUT_URL = "api/v1/accounts/logout/"

# SOCIAL_AUTH_PIPELINE = (
#     "social_core.pipeline.social_auth.social_details",
#     "social_core.pipeline.social_auth.social_uid",
#     "social_core.pipeline.social_auth.auth_allowed",
#     "social_core.pipeline.social_auth.social_user",
#     "social_core.pipeline.user.get_username",
#     # 'social_core.pipeline.social_auth.associate_by_email',
#     "social_core.pipeline.user.create_user",
#     "social_core.pipeline.social_auth.associate_user",
#     "social_core.pipeline.social_auth.load_extra_data",
#     "social_core.pipeline.user.user_details",
#     "user.pipeline.get_profile_image",
# )


# # Google
# SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", default="")
# SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", default="")
# SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
#     "https://www.googleapis.com/auth/userinfo.email",
#     "https://www.googleapis.com/auth/userinfo.profile",
# ]
#
# # Facebook
# SOCIAL_AUTH_FACEBOOK_API_VERSION = "13.0"
# SOCIAL_AUTH_FACEBOOK_KEY = env("SOCIAL_AUTH_FACEBOOK_KEY", default="")
# SOCIAL_AUTH_FACEBOOK_SECRET = env("SOCIAL_AUTH_FACEBOOK_SECRET", default="")
# SOCIAL_AUTH_FACEBOOK_SCOPE = ["email", "public_profile"]
# SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
#     "locale": "en_US",
#     "fields": "id, name, email, age_range",
# }

# AUTHENTICATION_BACKENDS = ('user.auth_backend.AuthBackend',)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
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
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
MESSAGING_SERVICE_SID = env("MESSAGING_SERVICE_SID")


# def show_toolbar(request):
#     return True
# DEBUG_TOOLBAR_CONFIG = {
#     "SHOW_TOOLBAR_CALLBACK": show_toolbar,
#     "INTERCEPT_REDIRECTS": False,
# }

CELERY_BROKER_URL = env("CELERY_BROKER")


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

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8020",
    "http://44.203.217.242:8020",
    "https://backend.tackapp.net",
    "http://172.31.8.161",
    "http://44.203.217.242",
]

STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# STRIPE_LIVE_SECRET_KEY = os.environ.get("STRIPE_LIVE_SECRET_KEY", "<your secret key>")
STRIPE_TEST_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_LIVE_MODE = False  # Change to True in production
# DJSTRIPE_WEBHOOK_SECRET = "whsec_xxx"  # Get it from the section in the Stripe dashboard where you added the webhook endpoint
DJSTRIPE_USE_NATIVE_JSONFIELD = True  # We recommend setting to True for new installations
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
# DJSTRIPE_WEBHOOK_VALIDATION = 'retrieve_event'
DJSTRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")


DWOLLA_APP_KEY = env('DWOLLA_APP_KEY')
DWOLLA_APP_SECRET = env('DWOLLA_APP_SECRET')
DWOLLA_WEBHOOK_SECRET = env('DWOLLA_WEBHOOK_SECRET')
DWOLLA_MAIN_FUNDING_SOURCE = env('DWOLLA_MAIN_FUNDING_SOURCE')
# CSRF_COOKIE_SECURE = False
PLAID_CLIENT_ID = env("PLAID_CLIENT_ID")
PLAID_CLIENT_SECRET = env("PLAID_CLIENT_SECRET")

S3_BUCKET_TACKAPPSTORAGE = env("S3_BUCKET_TACKAPPSTORAGE")
S3_BUCKET_CARDS = "/media/payment_methods/cards"
S3_BUCKET_BANKS = "/media/payment_methods/banks"
S3_BUCKET_DIGITAL_WALLETS = "/media/payment_methods/digital_wallets"
