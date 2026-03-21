"""Django-filter filters for Appointment resource."""
import django_filters
from .models import Appointment, AppointmentStatus, AppointmentModality


class AppointmentFilter(django_filters.FilterSet):
    professional = django_filters.UUIDFilter(field_name="professional__id")
    status = django_filters.ChoiceFilter(choices=AppointmentStatus.choices)
    modality = django_filters.ChoiceFilter(choices=AppointmentModality.choices)
    scheduled_after = django_filters.DateTimeFilter(
        field_name="scheduled_at", lookup_expr="gte"
    )
    scheduled_before = django_filters.DateTimeFilter(
        field_name="scheduled_at", lookup_expr="lte"
    )
    scheduled_date = django_filters.DateFilter(
        field_name="scheduled_at", lookup_expr="date"
    )

    class Meta:
        model = Appointment
        fields = ["professional", "status", "modality"]
