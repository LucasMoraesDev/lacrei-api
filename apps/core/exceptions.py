"""Centralized exception handling for consistent JSON error responses."""
import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("lacrei.error")


def custom_exception_handler(exc, context):
    """
    Custom exception handler that ensures all errors return a consistent
    JSON envelope:
        {
            "error": true,
            "code": "...",
            "message": "...",
            "details": {...}
        }
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "error": True,
            "code": _get_error_code(exc),
            "message": _get_message(response.data),
            "details": response.data,
        }

        request = context.get("request")
        if request:
            error_data["request_id"] = getattr(request, "request_id", None)

        if response.status_code >= 500:
            logger.error("Server error: %s", exc, exc_info=True)

        response.data = error_data

    return response


def _get_error_code(exc) -> str:
    if hasattr(exc, "default_code"):
        return exc.default_code
    return type(exc).__name__.lower()


def _get_message(data) -> str:
    if isinstance(data, dict):
        for key in ("detail", "non_field_errors"):
            if key in data:
                val = data[key]
                return str(val[0]) if isinstance(val, list) else str(val)
        first_value = next(iter(data.values()), "")
        return str(first_value[0]) if isinstance(first_value, list) else str(first_value)
    if isinstance(data, list):
        return str(data[0])
    return str(data)
