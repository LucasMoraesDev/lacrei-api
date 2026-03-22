"""Health check endpoint — used by load balancers and CI/CD pipelines."""

import time

from django.db import connection
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """
    Returns 200 if the application and database are reachable.
    Used by AWS ELB, GitHub Actions smoke tests, and uptime monitors.
    """
    start = time.monotonic()
    db_ok = False
    db_error = None

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = True
    except Exception as exc:
        db_error = str(exc)

    elapsed = round((time.monotonic() - start) * 1000, 2)
    status_code = 200 if db_ok else 503

    return JsonResponse(
        {
            "status": "healthy" if db_ok else "degraded",
            "database": "ok" if db_ok else f"error: {db_error}",
            "response_time_ms": elapsed,
            "version": "1.0.0",
        },
        status=status_code,
    )


urlpatterns = [
    path("", health_check, name="health_check"),
]
