"""
Appointment model for Lacrei Saúde API.

Each appointment is linked to a Professional via FK.
Cascade behaviour is PROTECT to prevent accidental data loss.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class AppointmentStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Agendada"
    CONFIRMED = "confirmed", "Confirmada"
    IN_PROGRESS = "in_progress", "Em andamento"
    COMPLETED = "completed", "Concluída"
    CANCELLED = "cancelled", "Cancelada"
    NO_SHOW = "no_show", "Não compareceu"


class AppointmentModality(models.TextChoices):
    IN_PERSON = "in_person", "Presencial"
    ONLINE = "online", "Online (Telemedicina)"
    HOME = "home", "Domiciliar"


class Appointment(models.Model):
    """Represents a medical appointment linked to a professional."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Relations ──────────────────────────────────────────────────────────────
    professional = models.ForeignKey(
        "professionals.Professional",
        on_delete=models.PROTECT,  # Do not cascade-delete appointments
        related_name="appointments",
        verbose_name="profissional",
        db_index=True,
    )

    # ── Scheduling ─────────────────────────────────────────────────────────────
    scheduled_at = models.DateTimeField("data e hora da consulta", db_index=True)
    duration_minutes = models.PositiveSmallIntegerField(
        "duração (minutos)", default=60, help_text="Duração estimada em minutos."
    )
    modality = models.CharField(
        "modalidade",
        max_length=20,
        choices=AppointmentModality.choices,
        default=AppointmentModality.IN_PERSON,
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
        db_index=True,
    )

    # ── Patient info (anonymized — no PII stored directly) ────────────────────
    patient_name = models.CharField("nome do paciente", max_length=255)
    patient_email = models.EmailField("e-mail do paciente", blank=True)
    patient_phone = models.CharField("telefone do paciente", max_length=20, blank=True)

    # ── Notes ──────────────────────────────────────────────────────────────────
    notes = models.TextField("observações", blank=True)
    cancellation_reason = models.TextField("motivo do cancelamento", blank=True)

    # ── Payment (Assas integration stub) ──────────────────────────────────────
    payment_id = models.CharField(
        "ID de pagamento (Assas)",
        max_length=100,
        blank=True,
        help_text="Referência externa da cobrança no Assas.",
    )
    payment_status = models.CharField(
        "status do pagamento",
        max_length=30,
        blank=True,
        help_text="Ex.: PENDING, CONFIRMED, REFUNDED",
    )

    # ── Metadata ───────────────────────────────────────────────────────────────
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["professional", "scheduled_at"]),
            models.Index(fields=["status", "scheduled_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"Consulta {self.id} — {self.professional.social_name} "
            f"em {self.scheduled_at.strftime('%d/%m/%Y %H:%M')}"
        )

    def clean(self) -> None:
        """Business rule: scheduled_at must be in the future for new appointments."""
        if self._state.adding and self.scheduled_at and self.scheduled_at <= timezone.now():
            raise ValidationError(
                {"scheduled_at": "A data da consulta deve ser no futuro."}
            )

    @property
    def is_cancellable(self) -> bool:
        return self.status in (AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED)
