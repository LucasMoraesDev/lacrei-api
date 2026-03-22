"""Django-filter filters for Professional resource."""

import django_filters

from .models import Professional, ProfessionChoices


class ProfessionalFilter(django_filters.FilterSet):
    profession = django_filters.ChoiceFilter(choices=ProfessionChoices.choices)
    city = django_filters.CharFilter(lookup_expr="icontains")
    state = django_filters.CharFilter(lookup_expr="iexact")
    is_active = django_filters.BooleanFilter()
    created_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Professional
        fields = ["profession", "city", "state", "is_active"]
