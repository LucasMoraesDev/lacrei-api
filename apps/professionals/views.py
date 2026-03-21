"""ViewSet for Professional resource."""
import logging
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Professional
from .serializers import ProfessionalSerializer, ProfessionalListSerializer
from .filters import ProfessionalFilter

logger = logging.getLogger("lacrei.access")


@extend_schema_view(
    list=extend_schema(
        summary="Listar profissionais",
        description="Retorna lista paginada de profissionais de saúde ativos.",
        tags=["professionals"],
    ),
    create=extend_schema(
        summary="Cadastrar profissional",
        description="Cria um novo profissional de saúde.",
        tags=["professionals"],
    ),
    retrieve=extend_schema(
        summary="Detalhar profissional",
        description="Retorna todos os dados de um profissional pelo UUID.",
        tags=["professionals"],
    ),
    update=extend_schema(
        summary="Atualizar profissional (completo)",
        tags=["professionals"],
    ),
    partial_update=extend_schema(
        summary="Atualizar profissional (parcial)",
        tags=["professionals"],
    ),
    destroy=extend_schema(
        summary="Remover profissional",
        description="Soft-delete: marca o profissional como inativo.",
        tags=["professionals"],
    ),
)
class ProfessionalViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para Profissionais de Saúde.

    - Listagem com filtros por profissão, cidade, estado e status.
    - Busca textual por nome social e email.
    - Soft-delete (is_active=False) para preservar histórico de consultas.
    """

    queryset = Professional.objects.all().order_by("social_name")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProfessionalFilter
    search_fields = ["social_name", "email", "city"]
    ordering_fields = ["social_name", "profession", "city", "created_at"]
    ordering = ["social_name"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProfessionalListSerializer
        return ProfessionalSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # By default show only active professionals; admin can pass ?is_active=all
        if self.request.query_params.get("is_active") != "all":
            qs = qs.filter(is_active=True)
        return qs

    def perform_destroy(self, instance: Professional) -> None:
        """Soft-delete: preserves referential integrity with appointments."""
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        logger.info("Professional soft-deleted: %s", instance.id)

    @extend_schema(
        summary="Consultas do profissional",
        description="Retorna todas as consultas vinculadas a este profissional.",
        tags=["professionals", "appointments"],
    )
    @action(detail=True, methods=["get"], url_path="appointments")
    def appointments(self, request, pk=None):
        """GET /professionals/{id}/appointments/ — busca por ID do profissional."""
        from apps.appointments.serializers import AppointmentSerializer
        professional = self.get_object()
        qs = professional.appointments.select_related("professional").order_by("-scheduled_at")
        serializer = AppointmentSerializer(qs, many=True, context={"request": request})
        return Response(
            {
                "professional_id": str(professional.id),
                "professional_name": professional.social_name,
                "count": qs.count(),
                "appointments": serializer.data,
            }
        )
