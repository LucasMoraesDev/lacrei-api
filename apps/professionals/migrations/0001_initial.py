"""Initial migration for Professional model."""
from django.db import migrations, models
import django.core.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Professional",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("social_name", models.CharField(help_text="Nome pelo qual o(a) profissional prefere ser chamado(a).", max_length=255, verbose_name="nome social")),
                ("profession", models.CharField(
                    choices=[
                        ("medico", "Médico(a)"), ("enfermeiro", "Enfermeiro(a)"),
                        ("psicologo", "Psicólogo(a)"), ("nutricionista", "Nutricionista"),
                        ("fisioterapeuta", "Fisioterapeuta"), ("dentista", "Dentista"),
                        ("farmaceutico", "Farmacêutico(a)"), ("assistente_social", "Assistente Social"),
                        ("terapeuta", "Terapeuta Ocupacional"), ("outro", "Outro"),
                    ],
                    db_index=True, max_length=50, verbose_name="profissão",
                )),
                ("council_number", models.CharField(blank=True, max_length=30, verbose_name="número do conselho (CRM, CRP, etc.)")),
                ("street", models.CharField(max_length=255, verbose_name="logradouro")),
                ("number", models.CharField(max_length=20, verbose_name="número")),
                ("complement", models.CharField(blank=True, max_length=100, verbose_name="complemento")),
                ("neighborhood", models.CharField(max_length=100, verbose_name="bairro")),
                ("city", models.CharField(max_length=100, verbose_name="cidade")),
                ("state", models.CharField(
                    max_length=2, verbose_name="estado (UF)",
                    validators=[django.core.validators.RegexValidator(r"^[A-Z]{2}$", "Use a sigla do estado (ex.: SP).")],
                )),
                ("postal_code", models.CharField(
                    max_length=9, verbose_name="CEP",
                    validators=[django.core.validators.RegexValidator(r"^\d{5}-?\d{3}$", "CEP inválido.")],
                )),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="e-mail")),
                ("phone", models.CharField(
                    max_length=20, verbose_name="telefone",
                    validators=[django.core.validators.RegexValidator(r"^[\d\s\+\(\)\-]{7,20}$", "Número de telefone inválido.")],
                )),
                ("whatsapp", models.CharField(
                    blank=True, max_length=20, verbose_name="WhatsApp",
                    validators=[django.core.validators.RegexValidator(r"^[\d\s\+\(\)\-]{7,20}$", "Número de telefone inválido.")],
                )),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
            ],
            options={"verbose_name": "Profissional de Saúde", "verbose_name_plural": "Profissionais de Saúde", "ordering": ["social_name"]},
        ),
        migrations.AddIndex(
            model_name="professional",
            index=models.Index(fields=["profession", "is_active"], name="professiona_profess_idx"),
        ),
        migrations.AddIndex(
            model_name="professional",
            index=models.Index(fields=["city", "state"], name="professiona_city_st_idx"),
        ),
    ]
