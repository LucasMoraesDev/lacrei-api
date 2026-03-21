"""Main URL configuration for Lacrei Saúde API."""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/", include([
        # Auth
        path("auth/", include("apps.core.urls.auth")),

        # Resources
        path("professionals/", include("apps.professionals.urls")),
        path("appointments/", include("apps.appointments.urls")),

        # Health check
        path("health/", include("apps.core.urls.health")),
    ])),

    # OpenAPI / Swagger / Redoc
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
