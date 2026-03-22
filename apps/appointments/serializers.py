"""Serializers for the Appointment resource."""

from django.utils import timezone
from rest_framework import serializers

from apps.core.sanitizers import sanitize_phone, sanitize_text
from apps.professionals.models import Professional

from .models import Appointment, AppointmentStatus


class AppointmentSerializer(serializers.ModelSerializer):
    """Full serializer — used for create, update, retrieve."""

    professional_name = serializers.CharField(
        source="professional.social_name", read_only=True
    )
    professional_profession = serializers.CharField(
        source="professional.get_profession_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    modality_display = serializers.CharField(
        source="get_modality_display", read_only=True
    )
    is_cancellable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "professional",
            "professional_name",
            "professional_profession",
            "scheduled_at",
            "duration_minutes",
            "modality",
            "modality_display",
            "status",
            "status_display",
            "patient_name",
            "patient_email",
            "patient_phone",
            "notes",
            "cancellation_reason",
            "payment_id",
            "payment_status",
            "is_cancellable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_professional(self, value: Professional) -> Professional:
        if not value.is_active:
            raise serializers.ValidationError(
                "Não é possível agendar consulta com profissional inativo."
            )
        return value

    def validate_scheduled_at(self, value):
        if self.instance is None and value <= timezone.now():
            raise serializers.ValidationError("A data da consulta deve ser no futuro.")
        return value

    def validate_duration_minutes(self, value: int) -> int:
        if not (15 <= value <= 480):
            raise serializers.ValidationError(
                "Duração deve ser entre 15 e 480 minutos."
            )
        return value

    def validate_patient_name(self, value: str) -> str:
        cleaned = sanitize_text(value)
        if len(cleaned) < 2:
            raise serializers.ValidationError(
                "Nome do paciente deve ter ao menos 2 caracteres."
            )
        return cleaned

    def validate_patient_phone(self, value: str) -> str:
        return sanitize_phone(value)

    def validate_notes(self, value: str) -> str:
        return sanitize_text(value)

    def validate_cancellation_reason(self, value: str) -> str:
        return sanitize_text(value)

    def validate(self, attrs):
        """Cross-field: cancellation_reason required when cancelling."""
        status = attrs.get("status", getattr(self.instance, "status", None))
        reason = attrs.get(
            "cancellation_reason", getattr(self.instance, "cancellation_reason", "")
        )
        if status == AppointmentStatus.CANCELLED and not reason:
            raise serializers.ValidationError(
                {"cancellation_reason": "Informe o motivo do cancelamento."}
            )
        return attrs


class AppointmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints."""

    professional_name = serializers.CharField(
        source="professional.social_name", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "professional",
            "professional_name",
            "scheduled_at",
            "status",
            "status_display",
            "patient_name",
            "modality",
        ]
