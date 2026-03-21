"""Custom authentication backends para Lacrei Saúde API."""
import logging
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger("lacrei.access")


class APIKeyUser:
    """
    Objeto que representa um cliente autenticado via API Key.
    Implementa a interface mínima que o DRF espera de request.user.
    """
    is_authenticated = True
    is_active = True

    def __str__(self):
        return "api-key-client"


class APIKeyAuthentication(BaseAuthentication):
    """
    Autenticação via header X-API-Key.
    Usado para comunicação service-to-service (ex.: integração Assas).
    """

    def authenticate(self, request):
        api_key = request.META.get(settings.API_KEY_HEADER, "").strip()
        if not api_key:
            return None  # Deixa outros autenticadores tentarem

        valid_keys = getattr(settings, "VALID_API_KEYS", [])
        if api_key not in valid_keys:
            logger.warning(
                "Tentativa com API key inválida",
                extra={"ip": self._get_client_ip(request), "key_prefix": api_key[:8]},
            )
            raise AuthenticationFailed("API Key inválida.")

        # Retorna (user, auth) — user implementa is_authenticated=True
        return (APIKeyUser(), {"type": "api_key", "key": api_key})

    def authenticate_header(self, request):
        return "X-API-Key"

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
