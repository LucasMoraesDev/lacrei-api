"""URL patterns for the professionals app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProfessionalViewSet

router = DefaultRouter()
router.register(r"", ProfessionalViewSet, basename="professional")

urlpatterns = [
    path("", include(router.urls)),
]
