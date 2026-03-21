"""Initial migration for Appointment model."""
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("professionals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("professional", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="appointments",
                    to="professionals.professional",
                    verbose_name="profissional",
                )),
                ("scheduled_at", models.DateTimeField(db_index=True, verbose_name="data e hora da consulta")),
                ("duration_minutes", models.PositiveSmallIntegerField(default=60, verbose_name="duração (minutos)")),
                ("modality", models.CharField(
                    choices=[("in_person", "Presencial"), ("online", "Online (Telemedicina)"), ("home", "Domiciliar")],
                    default="in_person", max_length=20, verbose_name="modalidade",
                )),
                ("status", models.CharField(
                    choices=[
                        ("scheduled", "Agendada"), ("confirmed", "Confirmada"),
                        ("in_progress", "Em andamento"), ("completed", "Concluída"),
                        ("cancelled", "Cancelada"), ("no_show", "Não compareceu"),
                    ],
                    db_index=True, default="scheduled", max_length=20, verbose_name="status",
                )),
                ("patient_name", models.CharField(max_length=255, verbose_name="nome do paciente")),
                ("patient_email", models.EmailField(blank=True, max_length=254, verbose_name="e-mail do paciente")),
                ("patient_phone", models.CharField(blank=True, max_length=20, verbose_name="telefone do paciente")),
                ("notes", models.TextField(blank=True, verbose_name="observações")),
                ("cancellation_reason", models.TextField(blank=True, verbose_name="motivo do cancelamento")),
                ("payment_id", models.CharField(blank=True, help_text="Referência externa da cobrança no Assas.", max_length=100, verbose_name="ID de pagamento (Assas)")),
                ("payment_status", models.CharField(blank=True, max_length=30, verbose_name="status do pagamento")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
            ],
            options={"verbose_name": "Consulta", "verbose_name_plural": "Consultas", "ordering": ["-scheduled_at"]},
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["professional", "scheduled_at"], name="appointmen_prof_sched_idx"),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["status", "scheduled_at"], name="appointmen_status_sched_idx"),
        ),
    ]
