"""Development settings."""

from .base import *  # noqa: F401, F403

DEBUG = True
SECRET_KEY = "dev-secret-key-not-for-production"

CORS_ALLOW_ALL_ORIGINS = True  # Only in dev!

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
