from urllib.parse import urlparse

from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = config("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY.startswith("change-me"):
    raise ImproperlyConfigured("SECRET_KEY must be a unique production value")

ALLOWED_HOSTS = [h for h in config("ALLOWED_HOSTS", default="", cast=Csv()) if h]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS is required in production")

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# TLS terminates in nginx. Keep False on Gunicorn so /healthz/ over HTTP works.
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
# HTTP test droplet: False. After SSL set both to True in .env.
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = [
    o for o in config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv()) if o
]

_db_url = config("DATABASE_URL", default="")
if not _db_url:
    raise ImproperlyConfigured("DATABASE_URL is required in production")
_u = urlparse(_db_url)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _u.path.lstrip("/"),
        "USER": _u.username,
        "PASSWORD": _u.password,
        "HOST": _u.hostname,
        "PORT": _u.port or 5432,
        "CONN_MAX_AGE": 60,
    }
}

# nginx serves /static/; hashed manifest is not required on the first HTTP droplet.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

_email_host = config("EMAIL_HOST", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@soliron.local")
if _email_host:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = _email_host
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
