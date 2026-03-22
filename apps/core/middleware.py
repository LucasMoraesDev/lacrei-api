"""Request logging middleware for Lacrei Saúde API."""

import logging
import time
import uuid

logger = logging.getLogger("lacrei.access")


class RequestLoggingMiddleware:
    """
    Logs every incoming request with timing, IP, method, path,
    and response status. Attaches a unique request_id for tracing.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        start = time.monotonic()

        response = self.get_response(request)

        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        logger.info(
            "HTTP %s %s → %s (%s ms)",
            request.method,
            request.get_full_path(),
            response.status_code,
            elapsed_ms,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.get_full_path(),
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
                "ip": self._get_client_ip(request),
                "user": str(getattr(request, "user", "anonymous")),
            },
        )
        response["X-Request-ID"] = request_id
        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
