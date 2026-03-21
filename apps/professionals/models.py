"""
Professional model for Lacrei Saúde API.

Stores healthcare professionals who can be linked to appointments.
All fields are sanitized at the serializer level before being persisted.
Django ORM uses parameterized queries — SQL injection is not possible.
"""
import uuid
from django.db import models
from django.core.validators import RegexValidator


class ProfessionChoices(models.TextChoices):
    MEDICO = "medico", "Médico(a)"
    ENFERMEIRO = "enfermeiro", "Enfermeiro(a)"
    PSICOLOGO = "psicologo", "Psicólogo(a)"
    NUTRICIONISTA = "nutricionista", "Nutricionista"
    FISIOTERAPEUTA = "fisioterapeuta", "Fisioterapeuta"
    DENTISTA = "dentista", "Dentista"
    FARMACEUTICO = "farmaceutico", "Farmacêutico(a)"
    ASSISTENTE_SOCIAL = "assistente_social", "Assistente Social"
    TERAPEUTA = "terapeuta", "Terapeuta Ocupacional"
    OUTRO = "outro", "Outro"


phone_validator = RegexValidator(
    regex=r"^[\d\s\+\(\)\-]{7,20}$",
    message="Número de telefone inválido.",
)

cep_validator = RegexValidator(
    regex=r"^\d{5}-?\d{3}$",
    message="CEP inválido. Use o formato 00000-000.",
)


class Professional(models.Model):
    """Represents a healthcare professional registered on the platform."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Identification ─────────────────────────────────────────────────────────
    social_name = models.CharField(
        "nome social",
        max_length=255,
        help_text="Nome pelo qual o(a) profissional prefere ser chamado(a).",
    )
    profession = models.CharField(
        "profissão",
        max_length=50,
        choices=ProfessionChoices.choices,
        db_index=True,
    )
    council_number = models.CharField(
        "número do conselho (CRM, CRP, etc.)",
        max_length=30,
        blank=True,
        help_text="Ex.: CRM/SP 123456",
    )

    # ── Address ────────────────────────────────────────────────────────────────
    street = models.CharField("logradouro", max_length=255)
    number = models.CharField("número", max_length=20)
    complement = models.CharField("complemento", max_length=100, blank=True)
    neighborhood = models.CharField("bairro", max_length=100)
    city = models.CharField("cidade", max_length=100)
    state = models.CharField(
        "estado (UF)",
        max_length=2,
        validators=[RegexValidator(r"^[A-Z]{2}$", "Use a sigla do estado (ex.: SP).")],
    )
    postal_code = models.CharField("CEP", max_length=9, validators=[cep_validator])

    # ── Contact ────────────────────────────────────────────────────────────────
    email = models.EmailField("e-mail", unique=True)
    phone = models.CharField("telefone", max_length=20, validators=[phone_validator])
    whatsapp = models.CharField(
        "WhatsApp", max_length=20, blank=True, validators=[phone_validator]
    )

    # ── Metadata ───────────────────────────────────────────────────────────────
    is_active = models.BooleanField("ativo", default=True, db_index=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Profissional de Saúde"
        verbose_name_plural = "Profissionais de Saúde"
        ordering = ["social_name"]
        indexes = [
            models.Index(fields=["profession", "is_active"]),
            models.Index(fields=["city", "state"]),
        ]

    def __str__(self) -> str:
        return f"{self.social_name} ({self.get_profession_display()})"

    @property
    def full_address(self) -> str:
        parts = [f"{self.street}, {self.number}"]
        if self.complement:
            parts.append(self.complement)
        parts.append(f"{self.neighborhood} — {self.city}/{self.state}")
        parts.append(self.postal_code)
        return ", ".join(parts)
