from decouple import config

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = config(
    "SECRET_KEY",
    default="dev-only-insecure-key-do-not-use-in-prod",
)
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

# Empty EMAIL_HOST → console. For Resend local test set EMAIL_* like production.
_email_host = config("EMAIL_HOST", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@soliron.local")
if _email_host:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = _email_host
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
    EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
