"""
Tests for the Appointment resource.

Covers:
- CRUD completo
- Validação de datas, duração e status
- Cancelamento com motivo
- Filtro por professional ID
- Testes de erro (dados ausentes, inválidos, profissional inativo)
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment, AppointmentStatus
from tests.factories import AppointmentFactory, ProfessionalFactory

API_KEY_HEADER = {"HTTP_X_API_KEY": "test-api-key"}


def future_dt(days: int = 7) -> str:
    return (timezone.now() + timedelta(days=days)).isoformat()


def past_dt(days: int = 1) -> str:
    return (timezone.now() - timedelta(days=days)).isoformat()


class AppointmentListTest(APITestCase):
    """Tests for GET /appointments/"""

    def setUp(self):
        self.url = reverse("appointment-list")
        self.prof_a = ProfessionalFactory()
        self.prof_b = ProfessionalFactory()
        AppointmentFactory.create_batch(3, professional=self.prof_a)
        AppointmentFactory.create_batch(2, professional=self.prof_b)

    def test_list_returns_all_appointments(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

    def test_filter_by_professional_id(self):
        response = self.client.get(
            self.url, {"professional": str(self.prof_a.id)}, **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_filter_by_status(self):
        AppointmentFactory(
            professional=self.prof_a,
            status=AppointmentStatus.CANCELLED,
            cancellation_reason="Teste",
        )
        response = self.client.get(self.url, {"status": "cancelled"}, **API_KEY_HEADER)
        self.assertEqual(response.data["count"], 1)

    def test_search_by_patient_name(self):
        appt = AppointmentFactory(
            professional=self.prof_a, patient_name="Fernanda UniquePatient"
        )
        response = self.client.get(
            self.url, {"search": "UniquePatient"}, **API_KEY_HEADER
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(appt.id))

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AppointmentCreateTest(APITestCase):
    """Tests for POST /appointments/"""

    def setUp(self):
        self.url = reverse("appointment-list")
        self.professional = ProfessionalFactory()
        self.valid_payload = {
            "professional": str(self.professional.id),
            "scheduled_at": future_dt(7),
            "duration_minutes": 60,
            "modality": "in_person",
            "patient_name": "João Oliveira",
            "patient_email": "joao@example.com",
            "patient_phone": "11988888888",
            "notes": "Primeira consulta.",
        }

    def test_create_appointment_with_valid_data(self):
        response = self.client.post(
            self.url, self.valid_payload, format="json", **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["status"], AppointmentStatus.SCHEDULED)

    def test_create_fails_without_required_fields(self):
        response = self.client.post(self.url, {}, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data["error"])

    def test_create_fails_with_past_date(self):
        payload = {**self.valid_payload, "scheduled_at": past_dt(1)}
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_fails_with_inactive_professional(self):
        inactive_prof = ProfessionalFactory(is_active=False)
        payload = {**self.valid_payload, "professional": str(inactive_prof.id)}
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_fails_with_invalid_duration(self):
        payload = {**self.valid_payload, "duration_minutes": 5}  # below minimum of 15
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_fails_with_nonexistent_professional(self):
        import uuid

        payload = {**self.valid_payload, "professional": str(uuid.uuid4())}
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_xss_in_patient_name_is_stripped(self):
        payload = {
            **self.valid_payload,
            "patient_name": "<img src=x onerror=alert(1)>Maria",
        }
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("<img", response.data["patient_name"])

    def test_create_fails_with_missing_patient_name(self):
        payload = {k: v for k, v in self.valid_payload.items() if k != "patient_name"}
        response = self.client.post(self.url, payload, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AppointmentRetrieveTest(APITestCase):
    """Tests for GET /appointments/{id}/"""

    def setUp(self):
        self.appointment = AppointmentFactory()
        self.url = reverse(
            "appointment-detail", kwargs={"pk": str(self.appointment.id)}
        )

    def test_retrieve_existing_appointment(self):
        response = self.client.get(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.appointment.id))
        self.assertIn("professional_name", response.data)
        self.assertIn("is_cancellable", response.data)

    def test_retrieve_nonexistent_returns_404(self):
        import uuid

        url = reverse("appointment-detail", kwargs={"pk": str(uuid.uuid4())})
        response = self.client.get(url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data["error"])


class AppointmentUpdateTest(APITestCase):
    """Tests for PATCH /appointments/{id}/"""

    def setUp(self):
        self.appointment = AppointmentFactory()
        self.url = reverse(
            "appointment-detail", kwargs={"pk": str(self.appointment.id)}
        )

    def test_partial_update_notes(self):
        response = self.client.patch(
            self.url,
            {"notes": "Paciente com alergia a penicilina."},
            format="json",
            **API_KEY_HEADER,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["notes"], "Paciente com alergia a penicilina.")

    def test_update_status_to_confirmed(self):
        response = self.client.patch(
            self.url, {"status": "confirmed"}, format="json", **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "confirmed")

    def test_cancel_without_reason_via_patch_returns_400(self):
        response = self.client.patch(
            self.url,
            {"status": "cancelled"},
            format="json",
            **API_KEY_HEADER,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AppointmentDeleteTest(APITestCase):
    """Tests for DELETE /appointments/{id}/ — soft-cancel."""

    def setUp(self):
        self.appointment = AppointmentFactory()
        self.url = reverse(
            "appointment-detail", kwargs={"pk": str(self.appointment.id)}
        )

    def test_delete_cancels_appointment(self):
        response = self.client.delete(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatus.CANCELLED)

    def test_delete_completed_appointment_returns_400(self):
        self.appointment.status = AppointmentStatus.COMPLETED
        self.appointment.save()
        response = self.client.delete(self.url, **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_appointment_still_exists_after_cancel(self):
        self.client.delete(self.url, **API_KEY_HEADER)
        self.assertTrue(Appointment.objects.filter(id=self.appointment.id).exists())


class AppointmentCancelActionTest(APITestCase):
    """Tests for PATCH /appointments/{id}/cancel/"""

    def setUp(self):
        self.appointment = AppointmentFactory()
        self.url = reverse(
            "appointment-cancel", kwargs={"pk": str(self.appointment.id)}
        )

    def test_cancel_with_reason_succeeds(self):
        response = self.client.patch(
            self.url,
            {"cancellation_reason": "Paciente desmarcou."},
            format="json",
            **API_KEY_HEADER,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")
        self.assertEqual(response.data["cancellation_reason"], "Paciente desmarcou.")

    def test_cancel_without_reason_returns_400(self):
        response = self.client.patch(self.url, {}, format="json", **API_KEY_HEADER)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_already_cancelled_returns_400(self):
        self.appointment.status = AppointmentStatus.CANCELLED
        self.appointment.cancellation_reason = "Cancelado."
        self.appointment.save()
        response = self.client.patch(
            self.url,
            {"cancellation_reason": "Tentar cancelar novamente."},
            format="json",
            **API_KEY_HEADER,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AppointmentByProfessionalTest(APITestCase):
    """Tests for GET /appointments/?professional={uuid} — requisito principal."""

    def setUp(self):
        self.prof = ProfessionalFactory()
        self.other = ProfessionalFactory()
        AppointmentFactory.create_batch(4, professional=self.prof)
        AppointmentFactory.create_batch(3, professional=self.other)
        self.url = reverse("appointment-list")

    def test_filter_returns_only_matching_professional(self):
        response = self.client.get(
            self.url, {"professional": str(self.prof.id)}, **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)
        for item in response.data["results"]:
            self.assertEqual(str(item["professional"]), str(self.prof.id))

    def test_invalid_uuid_returns_400(self):
        response = self.client.get(
            self.url, {"professional": "not-a-uuid"}, **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_professional_id_returns_empty_list(self):
        import uuid

        response = self.client.get(
            self.url, {"professional": str(uuid.uuid4())}, **API_KEY_HEADER
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
