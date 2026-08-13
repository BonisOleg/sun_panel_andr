from decouple import config

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = config(
    "SECRET_KEY",
    default="dev-only-insecure-key-do-not-use-in-prod",
)
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
