"""Admin registration for Professional model."""

from django.contrib import admin

from .models import Professional


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = [
        "social_name",
        "profession",
        "city",
        "state",
        "email",
        "is_active",
        "created_at",
    ]
    list_filter = ["profession", "state", "is_active"]
    search_fields = ["social_name", "email", "city"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["social_name"]
    list_per_page = 50

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "id",
                    "social_name",
                    "profession",
                    "council_number",
                    "is_active",
                )
            },
        ),
        (
            "Endereço",
            {
                "fields": (
                    "street",
                    "number",
                    "complement",
                    "neighborhood",
                    "city",
                    "state",
                    "postal_code",
                )
            },
        ),
        ("Contato", {"fields": ("email", "phone", "whatsapp")}),
        (
            "Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
