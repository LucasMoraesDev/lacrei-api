"""Factory Boy factories for test data generation."""

from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker import Faker

from apps.appointments.models import Appointment, AppointmentModality, AppointmentStatus
from apps.professionals.models import Professional, ProfessionChoices

fake = Faker("pt_BR")


class ProfessionalFactory(DjangoModelFactory):
    class Meta:
        model = Professional

    social_name = factory.LazyFunction(lambda: fake.name())
    profession = factory.Iterator([c.value for c in ProfessionChoices])
    council_number = factory.LazyFunction(lambda: f"CRM/SP {fake.numerify('######')}")
    street = factory.LazyFunction(lambda: fake.street_name())
    number = factory.LazyFunction(lambda: fake.building_number())
    complement = ""
    neighborhood = factory.LazyFunction(lambda: fake.bairro())
    city = factory.LazyFunction(lambda: fake.city())
    state = "SP"
    postal_code = factory.LazyFunction(lambda: fake.postcode())
    email = factory.LazyFunction(lambda: fake.unique.email())
    phone = factory.LazyFunction(lambda: fake.phone_number()[:20])
    whatsapp = ""
    is_active = True


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = Appointment

    professional = factory.SubFactory(ProfessionalFactory)
    scheduled_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    duration_minutes = 60
    modality = AppointmentModality.IN_PERSON
    status = AppointmentStatus.SCHEDULED
    patient_name = factory.LazyFunction(lambda: fake.name())
    patient_email = factory.LazyFunction(lambda: fake.email())
    patient_phone = factory.LazyFunction(lambda: fake.phone_number()[:20])
    notes = ""
    cancellation_reason = ""
