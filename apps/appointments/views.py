"""ViewSet for Appointment resource."""

import logging

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import AppointmentFilter
from .models import Appointment, AppointmentStatus
from .serializers import AppointmentListSerializer, AppointmentSerializer

logger = logging.getLogger("lacrei.access")


@extend_schema_view(
    list=extend_schema(
        summary="Listar consultas",
        description="Retorna lista paginada de consultas. Filtre por ?professional=<uuid> para buscar por profissional.",
        tags=["appointments"],
    ),
    create=extend_schema(
        summary="Agendar consulta",
        tags=["appointments"],
    ),
    retrieve=extend_schema(
        summary="Detalhar consulta",
        tags=["appointments"],
    ),
    update=extend_schema(
        summary="Atualizar consulta (completo)",
        tags=["appointments"],
    ),
    partial_update=extend_schema(
        summary="Atualizar consulta (parcial)",
        tags=["appointments"],
    ),
    destroy=extend_schema(
        summary="Cancelar consulta",
        description="Marca a consulta como CANCELLED. Não remove do banco.",
        tags=["appointments"],
    ),
)
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para Consultas Médicas.

    - Filtre por profissional: GET /appointments/?professional=<uuid>
    - Filtre por status: GET /appointments/?status=scheduled
    - Filtre por data: GET /appointments/?scheduled_after=2025-01-01
    - Ação de cancelamento: PATCH /appointments/{id}/cancel/
    """

    queryset = Appointment.objects.select_related("professional").order_by(
        "-scheduled_at"
    )
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AppointmentFilter
    search_fields = ["patient_name", "patient_email", "professional__social_name"]
    ordering_fields = ["scheduled_at", "status", "created_at"]
    ordering = ["-scheduled_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return AppointmentListSerializer
        return AppointmentSerializer

    def perform_destroy(self, instance: Appointment) -> None:
        """Soft-cancel instead of hard delete."""
        if not instance.is_cancellable:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                f"Consultas com status '{instance.get_status_display()}' não podem ser canceladas."
            )
        instance.status = AppointmentStatus.CANCELLED
        instance.save(update_fields=["status", "updated_at"])
        logger.info("Appointment cancelled: %s", instance.id)

    @extend_schema(
        summary="Cancelar consulta",
        description="Cancela a consulta informando obrigatoriamente o motivo.",
        tags=["appointments"],
        request={
            "application/json": {
                "type": "object",
                "properties": {"cancellation_reason": {"type": "string"}},
            }
        },
    )
    @action(detail=True, methods=["patch"], url_path="cancel")
    def cancel(self, request, pk=None):
        """PATCH /appointments/{id}/cancel/ — cancela com motivo."""
        appointment = self.get_object()
        if not appointment.is_cancellable:
            return Response(
                {"error": True, "message": "Esta consulta não pode ser cancelada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason = request.data.get("cancellation_reason", "").strip()
        if not reason:
            return Response(
                {"error": True, "message": "Informe o motivo do cancelamento."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancellation_reason = reason
        appointment.save(update_fields=["status", "cancellation_reason", "updated_at"])
        serializer = AppointmentSerializer(appointment, context={"request": request})
        return Response(serializer.data)
