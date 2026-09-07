from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from instruments.models import Instrument
from instruments.permissions import IsLMOOrAdmin, IsOfficer

from .models import VerificationApplication
from .serializers import VerificationApplicationSerializer


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

        # Generate application number
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

        # LMO and ADMIN can see all applications
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

        # LMO and ADMIN can open any application
        return queryset


# ============================================================
# LMO / ADMIN - ASSIGN APPLICATION TO LMO OR GATC
# ============================================================

class AssignApplicationView(APIView):
    permission_classes = [IsLMOOrAdmin]

    @transaction.atomic
    def patch(self, request, pk):

        # ----------------------------------------------------
        # IMPORTANT:
        # Lock ONLY the VerificationApplication row.
        #
        # Do NOT use select_related() together with
        # select_for_update() here because assigned_to is
        # nullable and PostgreSQL rejects the resulting
        # outer join with FOR UPDATE.
        # ----------------------------------------------------

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

        # Get officer ID from request
        officer_id = request.data.get("officer_id")

        if not officer_id:
            return Response(
                {
                    "officer_id": "This field is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Make sure selected user is an LMO or GATC
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

        # Assign application
        application.assigned_to = officer

        # Change status
        application.status = VerificationApplication.Status.ASSIGNED

        # Save changes
        application.save(
            update_fields=[
                "assigned_to",
                "status",
                "updated_at",
            ]
        )

        # Fetch related data normally AFTER the update
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