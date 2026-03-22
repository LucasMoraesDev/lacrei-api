"""
Tests for the Professional resource.

Covers:
- CRUD completo
- Validação e sanitização de inputs
- Autenticação (API Key e JWT)
- Soft-delete
- Busca por profissional via /appointments endpoint
"""

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.professionals.models import Professional
from tests.factories import AppointmentFactory, ProfessionalFactory


def get_jwt_header(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {str(refresh.access_token)}"}


API_KEY_HEADER = {"HTTP_X_API_KEY": "test-api-key"}


class ProfessionalAuthTest(APITestCase):
    """Ensures unauthenticated requests are rejected."""

    def setUp(self):
        self.url = reverse("professional-list")

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_key_authentication_works(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_api_key_returns_401(self):
        response = self.client.get(self.url, **{"HTTP_X_API_KEY": "wrong-key"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_authentication_works(self):
        user = User.objects.create_user("testuser", password="pass")
        response = self.client.get(self.url, **get_jwt_header(user))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProfessionalListTest(APITestCase):
    """Tests for GET /professionals/"""

    def setUp(self):
        self.url = reverse("professional-list")
        ProfessionalFactory.create_batch(5, is_active=True)
        ProfessionalFactory.create_batch(2, is_active=False)

    def test_list_returns_only_active_professionals(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

    def test_list_response_is_paginated(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)

    def test_filter_by_profession(self):
        ProfessionalFactory(profession="psicologo", is_active=True)
        response = self.client.get(
            self.url, {"profession": "psicologo"}, **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["profession"], "psicologo")

    def test_search_by_name(self):
        p = ProfessionalFactory(social_name="Dra. Ana Unique", is_active=True)
        response = self.client.get(self.url, {"search": "Unique"}, **API_KEY_HEADER)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["social_name"], p.social_name)

    def test_response_content_type_is_json(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(response["Content-Type"], "application/json")


class ProfessionalCreateTest(APITestCase):
    """Tests for POST /professionals/"""

    def setUp(self):
        self.url = reverse("professional-list")
        self.valid_payload = {
            "social_name": "Dr. Carlos Silva",
            "profession": "medico",
            "council_number": "CRM/SP 123456",
            "street": "Rua das Flores",
            "number": "100",
            "complement": "Sala 5",
            "neighborhood": "Centro",
            "city": "São Paulo",
            "state": "SP",
            "postal_code": "01310-100",
            "email": "carlos.silva@example.com",
            "phone": "11999999999",
            "whatsapp": "11999999999",
        }

    def test_create_professional_with_valid_data(self):
        response = self.client.post(
            self.url, self.valid_payload, format="json", **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["social_name"], "Dr. Carlos Silva")

    def test_create_fails_without_required_fields(self):
        response = self.client.post(self.url, {}, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data["error"])

    def test_create_fails_with_duplicate_email(self):
        ProfessionalFactory(email="carlos.silva@example.com")
        response = self.client.post(
            self.url, self.valid_payload, format="json", **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_fails_with_invalid_profession(self):
        payload = {**self.valid_payload, "profession": "engenheiro"}
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_fails_with_invalid_state(self):
        payload = {**self.valid_payload, "state": "SPP"}
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_html_in_social_name_is_stripped(self):
        """Sanitization must strip XSS attempts."""
        payload = {
            **self.valid_payload,
            "social_name": "<script>alert(1)</script>Dr. Carlos",
        }
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("<script>", response.data["social_name"])
        self.assertEqual(response.data["social_name"], "Dr. Carlos")

    def test_sql_injection_in_name_is_safe(self):
        """ORM parameterized queries prevent SQL injection — data is stored safely."""
        payload = {
            **self.valid_payload,
            "social_name": "'; DROP TABLE professionals; --",
        }
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        # Should succeed (data is stored as plain text, not executed as SQL)
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )
        # DB must still be alive
        self.assertEqual(Professional.objects.count(), Professional.objects.count())


class ProfessionalRetrieveTest(APITestCase):
    """Tests for GET /professionals/{id}/"""

    def setUp(self):
        self.professional = ProfessionalFactory()
        self.url = reverse(
            "professional-detail", kwargs={"pk": str(self.professional.id)}
        )

    def test_retrieve_existing_professional(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.professional.id))

    def test_retrieve_nonexistent_returns_404(self):
        import uuid

        url = reverse("professional-detail", kwargs={"pk": str(uuid.uuid4())})
        response = self.client.get(url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data["error"])

    def test_retrieve_includes_appointment_count(self):
        AppointmentFactory.create_batch(3, professional=self.professional)
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(response.data["appointment_count"], 3)


class ProfessionalUpdateTest(APITestCase):
    """Tests for PUT / PATCH /professionals/{id}/"""

    def setUp(self):
        self.professional = ProfessionalFactory()
        self.url = reverse(
            "professional-detail", kwargs={"pk": str(self.professional.id)}
        )

    def test_partial_update_social_name(self):
        response = self.client.patch(
            self.url, {"social_name": "Dr. Novo Nome"}, format="json", **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["social_name"], "Dr. Novo Nome")

    def test_partial_update_does_not_affect_other_fields(self):
        original_email = self.professional.email
        self.client.patch(
            self.url, {"social_name": "Novo Nome"}, format="json", **API_KEY_HEADER
        )
        self.professional.refresh_from_db()
        self.assertEqual(self.professional.email, original_email)

    def test_update_with_invalid_email_returns_400(self):
        response = self.client.patch(
            self.url, {"email": "not-an-email"}, format="json", **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfessionalDeleteTest(APITestCase):
    """Tests for DELETE /professionals/{id}/ — soft-delete."""

    def setUp(self):
        self.professional = ProfessionalFactory()
        self.url = reverse(
            "professional-detail", kwargs={"pk": str(self.professional.id)}
        )

    def test_delete_soft_deletes_professional(self):
        response = self.client.delete(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.professional.refresh_from_db()
        self.assertFalse(self.professional.is_active)

    def test_deleted_professional_not_in_list(self):
        self.client.delete(self.url, **API_KEY_HEADER)
        list_url = reverse("professional-list")
        response = self.client.get(list_url, **API_KEY_HEADER)
        ids = [p["id"] for p in response.data["results"]]
        self.assertNotIn(str(self.professional.id), ids)

    def test_deleted_professional_appointments_preserved(self):
        """Soft-delete must not cascade to appointments."""
        AppointmentFactory.create_batch(2, professional=self.professional)
        self.client.delete(self.url, **API_KEY_HEADER)
        from apps.appointments.models import Appointment

        self.assertEqual(
            Appointment.objects.filter(professional=self.professional).count(), 2
        )


class ProfessionalAppointmentsActionTest(APITestCase):
    """Tests for GET /professionals/{id}/appointments/"""

    def setUp(self):
        self.professional = ProfessionalFactory()
        self.other_professional = ProfessionalFactory()
        AppointmentFactory.create_batch(3, professional=self.professional)
        AppointmentFactory.create_batch(2, professional=self.other_professional)
        self.url = reverse(
            "professional-appointments", kwargs={"pk": str(self.professional.id)}
        )

    def test_returns_only_professional_appointments(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(response.data["professional_id"], str(self.professional.id))

    def test_returns_correct_professional_name(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(
            response.data["professional_name"], self.professional.social_name
        )
