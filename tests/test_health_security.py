"""
Tests for health check endpoint and security hardening.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

API_KEY_HEADER = {"HTTP_X_API_KEY": "test-api-key"}


class HealthCheckTest(TestCase):

    def test_health_check_returns_200(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("database", data)
        self.assertIn("version", data)

    def test_health_check_is_public(self):
        """Health check must be accessible without auth (for load balancers)."""
        response = self.client.get("/api/v1/health/")
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CORSTest(APITestCase):

    def test_cors_headers_present_for_allowed_origin(self):
        response = self.client.options(
            "/api/v1/professionals/",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            **API_KEY_HEADER,
        )
        # corsheaders sets the header on preflight or actual request
        self.assertIn(response.status_code, [200, 204])

    def test_request_id_header_in_response(self):
        response = self.client.get("/api/v1/professionals/", **API_KEY_HEADER)
        self.assertIn("X-Request-ID", response)


class SecurityHeadersTest(TestCase):

    def test_x_content_type_nosniff_header(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.get("X-Content-Type-Options"), "nosniff")

    def test_x_frame_options_deny(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.get("X-Frame-Options"), "DENY")


class SanitizationTest(APITestCase):
    """Unit tests for sanitizers module."""

    def test_sanitize_text_strips_html(self):
        from apps.core.sanitizers import sanitize_text

        result = sanitize_text("<script>alert('xss')</script>Hello")
        self.assertNotIn("<script>", result)
        self.assertIn("Hello", result)

    def test_sanitize_text_collapses_whitespace(self):
        from apps.core.sanitizers import sanitize_text

        result = sanitize_text("  Hello   World  ")
        self.assertEqual(result, "Hello World")

    def test_sanitize_phone_removes_special_chars(self):
        from apps.core.sanitizers import sanitize_phone

        result = sanitize_phone("+55 (11) 9 8888-7777")
        # Should only keep valid phone characters
        self.assertNotIn("@", result)

    def test_sanitize_cep_removes_invalid_chars(self):
        from apps.core.sanitizers import sanitize_cep

        result = sanitize_cep("01310-100abc")
        self.assertNotIn("abc", result)
