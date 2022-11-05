from pathlib import Path

from .admin_settings import (
    ALGORITHM,
    ALLOWED_HOSTS,
    AWS_ACCESS_KEY_ID,
    AWS_S3_ENDPOINT_URL,
    AWS_S3_REGION_NAME,
    AWS_SECRET_ACCESS_KEY,
    CORS_ALLOWED_ORIGINS,
    DATABASES,
    DEFAULT_POST_IMAGE_URL,
    DEFAULT_USER_THUMBNAIL_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_PROFILE_URI,
    GOOGLE_REDIRECT_URI,
    GOOGLE_RESPONSE_TYPE,
    GOOGLE_SCOPE,
    KAKAO_DEFAULT_EMAIL,
    KAKAO_PROFILE_URI,
    KAKAO_REDIRECT_URI,
    KAKAO_REST_API_KEY,
    MONGODB_ADDRESS,
    PASSWORD_HASHERS,
    PASSWORD_SALT,
    POST_IMAGES_URL,
    PROFILE_IMAGES_URL,
    SECRET_KEY,
)
from .bad_words import BAD_WORDS_LIST

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# use a secure cookie for the CSRF token cookie
# CSRF_COOKIE_SECURE = True
# CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# ssl settings
# SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60  # 1 minute
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY
DATABASES = DATABASES

# production setting
ALLOWED_HOSTS = ALLOWED_HOSTS
DEBUG = True

# SECURITY WARNING: don't run with debug turned on in production!
# ALLOWED_HOSTS = ["*"]
# DEBUG = True

PASSWORD_SALT = PASSWORD_SALT
PASSWORD_HASHERS = PASSWORD_HASHERS
ALGORITHM = ALGORITHM

APPEND_SLASH = False

# for Django debug toolbar and Django Ninja
# INTERNAL_IPS = ["127.0.0.1"]
# RENDER_PANELS = True

# If using Docker the following will set your INTERNAL_IPS correctly in Debug mode:
# if DEBUG:
#     import socket
#     hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
#     INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "debug_toolbar",
    # 'sslserver',
    "corsheaders",
    "django_extensions",
    "django.contrib.postgres",
    "socketio",
    "cores",
    "users",
    "posts",
    "comments",
    "chat",
]

MIDDLEWARE = [
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cores.middleware.PutPatchWithFileFormMiddleware",
]

# CORS
CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOW_ALL_ORIGINS = True

# production setting
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS

CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "Access-Control-Allow-Headers",
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
# ASGI_APPLICATION = 'togedog_dj.asgi.application'

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
# STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

BAD_WORDS_LIST = BAD_WORDS_LIST

# AWS S3
AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
AWS_S3_REGION_NAME = AWS_S3_REGION_NAME
AWS_S3_ENDPOINT_URL = AWS_S3_ENDPOINT_URL

POST_IMAGES_URL = POST_IMAGES_URL
PROFILE_IMAGES_URL = PROFILE_IMAGES_URL
DEFAULT_USER_THUMBNAIL_URL = DEFAULT_USER_THUMBNAIL_URL
DEFAULT_POST_IMAGE_URL = DEFAULT_POST_IMAGE_URL

# Social Login
KAKAO_REDIRECT_URI = KAKAO_REDIRECT_URI
KAKAO_REST_API_KEY = KAKAO_REST_API_KEY
KAKAO_DEFAULT_EMAIL = KAKAO_DEFAULT_EMAIL
KAKAO_PROFILE_URI = KAKAO_PROFILE_URI

GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = GOOGLE_REDIRECT_URI
GOOGLE_RESPONSE_TYPE = GOOGLE_RESPONSE_TYPE
GOOGLE_SCOPE = GOOGLE_SCOPE
GOOGLE_PROFILE_URI = GOOGLE_PROFILE_URI

# MongoDB
MONGODB_ADDRESS = MONGODB_ADDRESS
