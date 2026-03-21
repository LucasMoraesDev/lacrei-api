"""Staging settings — mirrors production but with relaxed SSL."""
from .production import *  # noqa: F401, F403
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from decouple import config

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

if SENTRY_DSN:  # noqa: F405
    sentry_sdk.init(
        dsn=SENTRY_DSN,  # noqa: F405
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=False,
        environment="staging",
    )
