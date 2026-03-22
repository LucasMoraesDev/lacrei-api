"""
Serializers for the Professional resource.

All incoming string fields are sanitized with bleach to prevent
XSS, and the ORM's parameterized queries prevent SQL injection.
"""

from rest_framework import serializers

from apps.core.sanitizers import sanitize_cep, sanitize_phone, sanitize_text

from .models import Professional, ProfessionChoices


class ProfessionalSerializer(serializers.ModelSerializer):
    """Full serializer — used for create, update, retrieve."""

    profession_display = serializers.CharField(
        source="get_profession_display", read_only=True
    )
    full_address = serializers.CharField(read_only=True)
    appointment_count = serializers.SerializerMethodField()

    class Meta:
        model = Professional
        fields = [
            "id",
            "social_name",
            "profession",
            "profession_display",
            "council_number",
            "street",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
            "postal_code",
            "full_address",
            "email",
            "phone",
            "whatsapp",
            "is_active",
            "appointment_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_appointment_count(self, obj) -> int:
        return obj.appointments.count()

    # ── Sanitization ──────────────────────────────────────────────────────────

    def validate_social_name(self, value: str) -> str:
        cleaned = sanitize_text(value)
        if len(cleaned) < 2:
            raise serializers.ValidationError(
                "Nome social deve ter ao menos 2 caracteres."
            )
        return cleaned

    def validate_council_number(self, value: str) -> str:
        return sanitize_text(value)

    def validate_street(self, value: str) -> str:
        return sanitize_text(value)

    def validate_number(self, value: str) -> str:
        return sanitize_text(value)

    def validate_complement(self, value: str) -> str:
        return sanitize_text(value)

    def validate_neighborhood(self, value: str) -> str:
        return sanitize_text(value)

    def validate_city(self, value: str) -> str:
        return sanitize_text(value)

    def validate_state(self, value: str) -> str:
        cleaned = sanitize_text(value).upper()
        if len(cleaned) != 2:
            raise serializers.ValidationError(
                "Use a sigla do estado com 2 letras (ex.: SP)."
            )
        return cleaned

    def validate_postal_code(self, value: str) -> str:
        return sanitize_cep(value)

    def validate_phone(self, value: str) -> str:
        return sanitize_phone(value)

    def validate_whatsapp(self, value: str) -> str:
        return sanitize_phone(value)

    def validate_profession(self, value: str) -> str:
        valid = [c.value for c in ProfessionChoices]
        if value not in valid:
            raise serializers.ValidationError(
                f"Profissão inválida. Opções: {', '.join(valid)}"
            )
        return value


class ProfessionalListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints."""

    profession_display = serializers.CharField(
        source="get_profession_display", read_only=True
    )

    class Meta:
        model = Professional
        fields = [
            "id",
            "social_name",
            "profession",
            "profession_display",
            "city",
            "state",
            "email",
            "is_active",
        ]
