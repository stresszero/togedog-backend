from pathlib import Path

from .admin_settings import (
    SECRET_KEY, 
    DATABASES, 
    PASSWORD_HASHERS, 
    PASSWORD_SALT, 
    ALGORITHM,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_ENDPOINT_URL,
    AWS_S3_REGION_NAME,
    KAKAO_REDIRECT_URI,
    KAKAO_REST_API_KEY,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_RESPONSE_TYPE,
    GOOGLE_SCOPE,
    POST_IMAGES_URL,
    PROFILE_IMAGES_URL
    )

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# Channels
ASGI_APPLICATION = 'togedog_dj.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY
DATABASES = DATABASES

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

PASSWORD_SALT = PASSWORD_SALT
PASSWORD_HASHERS = PASSWORD_HASHERS 
ALGORITHM = ALGORITHM

ALLOWED_HOSTS = ["*"]

APPEND_SLASH = False

# Application definition

INSTALLED_APPS = [
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_extensions",
    "django.contrib.postgres",
    "cores",
    "users",
    "posts",
    "comments",
    "chat"
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cores.middleware.PutPatchWithFileFormMiddleware"
    # "django.middleware.csrf.CsrfViewMiddleware",
]

##CORS
CORS_ORIGIN_ALLOW_ALL=True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
)

CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)

ROOT_URLCONF = "togedog_dj.urls"

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

WSGI_APPLICATION = "togedog_dj.wsgi.application"



# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# AWS S3
AWS_ACCESS_KEY_ID     = AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
AWS_S3_REGION_NAME    = AWS_S3_REGION_NAME
AWS_S3_ENDPOINT_URL   = AWS_S3_ENDPOINT_URL

# Social Login
KAKAO_REDIRECT_URI = KAKAO_REDIRECT_URI
KAKAO_REST_API_KEY = KAKAO_REST_API_KEY

GOOGLE_CLIENT_ID     = GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI  = GOOGLE_REDIRECT_URI
GOOGLE_RESPONSE_TYPE = GOOGLE_RESPONSE_TYPE
GOOGLE_SCOPE         = GOOGLE_SCOPE

# runserver logging
LOGGING = {
    'disable_existing_loggers': False,
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}