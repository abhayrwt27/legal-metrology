from django.db import IntegrityError
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from instruments.models import Instrument

from .models import VerificationApplication
from .serializers import VerificationApplicationSerializer


class VerificationApplicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerificationApplicationSerializer

    def get_queryset(self):
        return (
            VerificationApplication.objects
            .filter(applicant=self.request.user)
            .select_related("instrument")
            .order_by("-submitted_at")
        )

    def perform_create(self, serializer):
        instrument_id = self.request.data.get("instrument")

        try:
            instrument = Instrument.objects.get(
                id=instrument_id,
                owner=self.request.user,
            )
        except Instrument.DoesNotExist:
            raise ValueError(
                "The selected instrument does not exist or does not belong to you."
            )

        application_number = self.generate_application_number()

        serializer.save(
            applicant=self.request.user,
            instrument=instrument,
            application_number=application_number,
        )

    def generate_application_number(self):
        last_application = (
            VerificationApplication.objects
            .order_by("-id")
            .first()
        )

        if last_application:
            last_id = last_application.id + 1
        else:
            last_id = 1

        return f"VAPP-{last_id:06d}"


class VerificationApplicationDetailView(
    generics.RetrieveAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = VerificationApplicationSerializer

    def get_queryset(self):
        return (
            VerificationApplication.objects
            .filter(applicant=self.request.user)
            .select_related("instrument")
        )
