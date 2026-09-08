from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from instruments.models import Instrument
from instruments.permissions import IsGATC, IsLMOOrAdmin, IsOfficer

from .models import Inspection, VerificationApplication
from .serializers import (
    InspectionSerializer,
    VerificationApplicationSerializer,
)


User = get_user_model()


# ============================================================
# OWNER - LIST & CREATE VERIFICATION APPLICATION
# ============================================================

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
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "instrument": (
                        "The selected instrument does not exist "
                        "or does not belong to you."
                    )
                }
            )

        last_application = (
            VerificationApplication.objects
            .order_by("-id")
            .first()
        )

        if last_application:
            next_id = last_application.id + 1
        else:
            next_id = 1

        application_number = f"VAPP-{next_id:06d}"

        serializer.save(
            applicant=self.request.user,
            instrument=instrument,
            application_number=application_number,
        )


# ============================================================
# OWNER - VIEW SINGLE APPLICATION
# ============================================================

class VerificationApplicationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerificationApplicationSerializer

    def get_queryset(self):
        return (
            VerificationApplication.objects
            .filter(applicant=self.request.user)
            .select_related("instrument")
        )


# ============================================================
# LMO / GATC / ADMIN - VIEW APPLICATIONS
# ============================================================

class OfficerApplicationListView(generics.ListAPIView):
    permission_classes = [IsOfficer]
    serializer_class = VerificationApplicationSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = (
            VerificationApplication.objects
            .select_related(
                "instrument",
                "applicant",
                "assigned_to",
            )
            .order_by("-submitted_at")
        )

        # GATC can only see applications assigned to them
        if user.role == "GATC":
            queryset = queryset.filter(assigned_to=user)

        return queryset


# ============================================================
# LMO / GATC / ADMIN - VIEW SINGLE APPLICATION
# ============================================================

class OfficerApplicationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsOfficer]
    serializer_class = VerificationApplicationSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = (
            VerificationApplication.objects
            .select_related(
                "instrument",
                "applicant",
                "assigned_to",
            )
        )

        # GATC can only open applications assigned to them
        if user.role == "GATC":
            queryset = queryset.filter(assigned_to=user)

        return queryset


# ============================================================
# LMO / ADMIN - ASSIGN APPLICATION TO LMO OR GATC
# ============================================================

class AssignApplicationView(APIView):
    permission_classes = [IsLMOOrAdmin]

    @transaction.atomic
    def patch(self, request, pk):

        # Lock only the application row.
        # This avoids PostgreSQL's nullable outer-join
        # FOR UPDATE problem.

        try:
            application = (
                VerificationApplication.objects
                .select_for_update()
                .get(pk=pk)
            )

        except VerificationApplication.DoesNotExist:
            return Response(
                {
                    "detail": "Verification application not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        officer_id = request.data.get("officer_id")

        if not officer_id:
            return Response(
                {
                    "officer_id": "This field is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            officer = User.objects.get(
                id=officer_id,
                role__in=["LMO", "GATC"],
            )

        except User.DoesNotExist:
            return Response(
                {
                    "officer_id": (
                        "The selected user is not a valid "
                        "LMO or GATC officer."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.assigned_to = officer
        application.status = VerificationApplication.Status.ASSIGNED

        application.save(
            update_fields=[
                "assigned_to",
                "status",
                "updated_at",
            ]
        )

        application = (
            VerificationApplication.objects
            .select_related(
                "instrument",
                "applicant",
                "assigned_to",
            )
            .get(pk=application.pk)
        )

        serializer = VerificationApplicationSerializer(
            application
        )

        return Response(
            {
                "message": "Application assigned successfully.",
                "application": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# GATC - CREATE INSPECTION
# ============================================================

class GATCInspectionCreateView(generics.CreateAPIView):
    permission_classes = [IsGATC]
    serializer_class = InspectionSerializer

    def perform_create(self, serializer):
        application = serializer.validated_data["application"]

        # Make sure this application is actually assigned
        # to the logged-in GATC.
        if application.assigned_to != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "This application is not assigned to you."
            )

        # Prevent multiple inspections for the same application.
        if Inspection.objects.filter(
            application=application
        ).exists():
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "application": (
                        "An inspection already exists "
                        "for this application."
                    )
                }
            )

        # Move application into inspection stage.
        application.status = (
            VerificationApplication.Status.INSPECTION
        )
        application.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        serializer.save(
            inspector=self.request.user
        )


# ============================================================
# GATC - VIEW OWN INSPECTION
# ============================================================

class GATCInspectionDetailView(generics.RetrieveAPIView):
    permission_classes = [IsGATC]
    serializer_class = InspectionSerializer

    def get_queryset(self):
        return (
            Inspection.objects
            .filter(inspector=self.request.user)
            .select_related(
                "application",
                "inspector",
            )
        )