"""Pytest configuration and shared fixtures."""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tests.factories import ProfessionalFactory, AppointmentFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_key_client():
    client = APIClient()
    client.credentials(HTTP_X_API_KEY="test-api-key")
    return client


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def jwt_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def professional(db):
    return ProfessionalFactory()


@pytest.fixture
def appointment(db):
    return AppointmentFactory()
