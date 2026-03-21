"""Admin registration for Appointment model."""
from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["id", "professional", "patient_name", "scheduled_at", "status", "modality", "created_at"]
    list_filter = ["status", "modality", "scheduled_at"]
    search_fields = ["patient_name", "patient_email", "professional__social_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-scheduled_at"]
    list_per_page = 50
    raw_id_fields = ["professional"]

    fieldsets = (
        ("Agendamento", {"fields": ("id", "professional", "scheduled_at", "duration_minutes", "modality", "status")}),
        ("Paciente", {"fields": ("patient_name", "patient_email", "patient_phone")}),
        ("Observações", {"fields": ("notes", "cancellation_reason")}),
        ("Pagamento", {"fields": ("payment_id", "payment_status"), "classes": ("collapse",)}),
        ("Auditoria", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
