from datetime import date, timedelta
from io import BytesIO

import qrcode

from django.db import models, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from instruments.models import Instrument
from instruments.permissions import IsGATC, IsLMOOrAdmin, IsOfficer

from .models import (
    Certificate,
    Inspection,
    VerificationApplication,
    VerificationSchedule,
    VerificationDocument,
)
from .serializers import (
    InspectionSerializer,
    VerificationApplicationSerializer,
    VerificationScheduleSerializer,
    PublicInstrumentVerificationSerializer,
    VerificationDocumentSerializer,
)


# ============================================================
# OWNER - VERIFICATION APPLICATIONS
# ============================================================

class VerificationApplicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerificationApplicationSerializer

    def get_queryset(self):
        return (
            VerificationApplication.objects
            .filter(applicant=self.request.user)
            .select_related("instrument", "assigned_to", "previous_application")
            .order_by("-submitted_at")
        )

    def perform_create(self, serializer):
        instrument_id = self.request.data.get("instrument")

        instrument = get_object_or_404(
            Instrument,
            id=instrument_id,
            owner=self.request.user,
        )

        last_application = (
            VerificationApplication.objects
            .order_by("-id")
            .first()
        )

        if last_application:
            next_number = last_application.id + 1
        else:
            next_number = 1

        application_number = f"VAPP-{next_number:06d}"

        serializer.save(
            applicant=self.request.user,
            instrument=instrument,
            application_number=application_number,
        )



class VerificationApplicationDetailView(
    generics.RetrieveAPIView
):
    permission_classes = [IsAuthenticated]
    serializer_class = VerificationApplicationSerializer

    def get_queryset(self):
        return (
            VerificationApplication.objects
            .filter(applicant=self.request.user)
            .select_related("instrument", "assigned_to")
        )


# ============================================================
# OFFICER - APPLICATION LIST
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

        # GATC sees only applications assigned to itself
        if user.role == "GATC":
            queryset = queryset.filter(assigned_to=user)

        return queryset


# ============================================================
# OFFICER - APPLICATION DETAIL
# ============================================================

class OfficerApplicationDetailView(
    generics.RetrieveAPIView
):
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

        if user.role == "GATC":
            queryset = queryset.filter(assigned_to=user)

        return queryset


# ============================================================
# LMO / ADMIN - ASSIGN APPLICATION
# ============================================================

class AssignApplicationView(APIView):
    permission_classes = [IsLMOOrAdmin]

    def patch(self, request, pk):
        officer_id = request.data.get("officer_id")

        if not officer_id:
            return Response(
                {"error": "officer_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Lock only the application row.
        # Do NOT use select_related with select_for_update
        # because assigned_to is nullable in PostgreSQL.
        with transaction.atomic():
            try:
                application = (
                    VerificationApplication.objects
                    .select_for_update()
                    .get(pk=pk)
                )
            except VerificationApplication.DoesNotExist:
                return Response(
                    {"error": "Application not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            from django.contrib.auth import get_user_model

            User = get_user_model()

            try:
                officer = User.objects.get(
                    pk=officer_id,
                    role="GATC",
                )
            except User.DoesNotExist:
                return Response(
                    {
                        "error":
                        "Selected officer does not exist or is not a GATC."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if application.status not in [
                VerificationApplication.Status.SUBMITTED,
                VerificationApplication.Status.UNDER_REVIEW,
                VerificationApplication.Status.ASSIGNED,
            ]:
                return Response(
                    {
                        "error":
                        "This application cannot be assigned "
                        "in its current status."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            application.assigned_to = officer
            application.status = (
                VerificationApplication.Status.ASSIGNED
            )
            application.save(
                update_fields=[
                    "assigned_to",
                    "status",
                    "updated_at",
                ]
            )

        return Response(
            {
                "message": "Application assigned successfully.",
                "application": VerificationApplicationSerializer(
                    application
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# LMO / ADMIN - SCHEDULE VERIFICATION
# ============================================================

class VerificationScheduleCreateView(generics.CreateAPIView):
    permission_classes = [IsLMOOrAdmin]
    serializer_class = VerificationScheduleSerializer

    def perform_create(self, serializer):
        application = serializer.validated_data["application"]

        # Prevent scheduling an application that is already
        # approved or rejected.
        if application.status not in [
            VerificationApplication.Status.ASSIGNED,
            VerificationApplication.Status.SCHEDULED,
        ]:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                "Only assigned applications can be scheduled."
            )

        schedule = serializer.save(
            scheduled_by=self.request.user,
        )

        # Mark application as scheduled.
        application.status = (
            VerificationApplication.Status.SCHEDULED
        )

        application.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


# ============================================================
# GATC - CREATE INSPECTION
# ============================================================

class GATCInspectionCreateView(generics.CreateAPIView):
    permission_classes = [IsGATC]
    serializer_class = InspectionSerializer

    def perform_create(self, serializer):
        inspection = serializer.save(
            inspector=self.request.user
        )

        application = inspection.application

        application.status = (
            VerificationApplication.Status.INSPECTION
        )
        application.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


# ============================================================
# GATC - INSPECTION DETAIL
# ============================================================

class GATCInspectionDetailView(
    generics.RetrieveUpdateAPIView
):
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


# ============================================================
# LMO / ADMIN - APPROVE OR REJECT APPLICATION
# ============================================================

class ApplicationDecisionView(APIView):
    permission_classes = [IsLMOOrAdmin]

    def patch(self, request, pk):
        decision = request.data.get("decision")
        remarks = request.data.get("remarks", "")

        if decision not in [
            VerificationApplication.Status.APPROVED,
            VerificationApplication.Status.REJECTED,
        ]:
            return Response(
                {
                    "error":
                    "Decision must be APPROVED or REJECTED."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():

            # Lock ONLY the application row.
            # This avoids PostgreSQL's nullable-side
            # FOR UPDATE problem.
            try:
                application = (
                    VerificationApplication.objects
                    .select_for_update()
                    .get(pk=pk)
                )
            except VerificationApplication.DoesNotExist:
                return Response(
                    {"error": "Application not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if application.status not in [
                VerificationApplication.Status.INSPECTION,
                VerificationApplication.Status.ASSIGNED,
            ]:
                return Response(
                    {
                        "error":
                        "This application cannot be decided "
                        "in its current status."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            application.remarks = remarks

            # ------------------------------------------------
            # REJECT
            # ------------------------------------------------

            if decision == VerificationApplication.Status.REJECTED:

                application.status = (
                    VerificationApplication.Status.REJECTED
                )

                application.save(
                    update_fields=[
                        "status",
                        "remarks",
                        "updated_at",
                    ]
                )

                return Response(
                    {
                        "message":
                        "Application rejected successfully.",
                        "application":
                        VerificationApplicationSerializer(
                            application
                        ).data,
                    },
                    status=status.HTTP_200_OK,
                )

            # ------------------------------------------------
            # APPROVE
            # ------------------------------------------------

            application.status = (
                VerificationApplication.Status.APPROVED
            )

            application.save(
                update_fields=[
                    "status",
                    "remarks",
                    "updated_at",
                ]
            )

            # ------------------------------------------------
            # CREATE CERTIFICATE
            # ------------------------------------------------

            existing_certificate = (
                Certificate.objects
                .filter(application=application)
                .first()
            )

            if existing_certificate:
                certificate = existing_certificate
            else:

                last_certificate = (
                    Certificate.objects
                    .order_by("-id")
                    .first()
                )

                if last_certificate:
                    next_number = last_certificate.id + 1
                else:
                    next_number = 1

                certificate_number = (
                    f"CERT-{next_number:06d}"
                )

                issue_date = date.today()

                valid_until = (
                    issue_date + timedelta(days=365)
                )

                certificate = Certificate.objects.create(
                    application=application,
                    certificate_number=certificate_number,
                    instrument=application.instrument,
                    owner=application.applicant,
                    issued_by=request.user,
                    issue_date=issue_date,
                    valid_until=valid_until,
                    status=Certificate.Status.VALID,
                    remarks=remarks,
                )

        return Response(
            {
                "message":
                "Application approved and certificate "
                "generated successfully.",
                "application":
                VerificationApplicationSerializer(
                    application
                ).data,
                "certificate": {
                    "id": certificate.id,
                    "certificate_number":
                        certificate.certificate_number,
                    "application":
                        certificate.application_id,
                    "instrument":
                        certificate.instrument_id,
                    "owner":
                        certificate.owner_id,
                    "issued_by":
                        certificate.issued_by_id,
                    "issue_date":
                        certificate.issue_date,
                    "valid_until":
                        certificate.valid_until,
                    "status":
                        certificate.status,
                    "remarks":
                        certificate.remarks,
                },
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# CERTIFICATE - RETRIEVE
# ============================================================

class CertificateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            certificate = (
                Certificate.objects
                .select_related(
                    "application",
                    "instrument",
                    "owner",
                    "issued_by",
                )
                .get(pk=pk)
            )
        except Certificate.DoesNotExist:
            return Response(
                {"error": "Certificate not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Owner can view their certificate.
        # Issuing LMO/Admin can also view it.
        if (
            request.user != certificate.owner
            and request.user != certificate.issued_by
            and request.user.role != "ADMIN"
        ):
            return Response(
                {"error": "You do not have permission to view this certificate."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "id": certificate.id,
                "certificate_number":
                    certificate.certificate_number,
                "application_number":
                    certificate.application.application_number,
                "instrument": {
                    "id":
                        certificate.instrument.id,
                    "name":
                        certificate.instrument.name,
                    "instrument_type":
                        certificate.instrument.instrument_type,
                    "manufacturer":
                        certificate.instrument.manufacturer,
                    "model_number":
                        certificate.instrument.model_number,
                    "serial_number":
                        certificate.instrument.serial_number,
                },
                "owner": {
                    "id":
                        certificate.owner.id,
                    "username":
                        certificate.owner.username,
                    "email":
                        certificate.owner.email,
                },
                "issued_by": {
                    "id":
                        certificate.issued_by.id,
                    "username":
                        certificate.issued_by.username,
                    "role":
                        certificate.issued_by.role,
                },
                "issue_date":
                    certificate.issue_date,
                "valid_until":
                    certificate.valid_until,
                "status":
                    certificate.status,
                "remarks":
                    certificate.remarks,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# CERTIFICATE - EXPIRY ALERTS
# ============================================================

class CertificateExpiryAlertView(APIView):
    """
    Returns certificate expiry information.

    OWNER:
        Sees only their own certificates.

    LMO / ADMIN:
        Sees certificates from all owners.

    Expiry categories:
        EXPIRED
        EXPIRING_SOON  -> expires within 30 days
        VALID          -> more than 30 days remaining
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()

        queryset = (
            Certificate.objects
            .select_related(
                "instrument",
                "owner",
            )
            .order_by("valid_until")
        )

        # OWNER sees only their certificates.
        if request.user.role == "OWNER":
            queryset = queryset.filter(owner=request.user)

        # LMO / ADMIN can see all certificates.
        elif request.user.role in ["LMO", "ADMIN"]:
            pass

        else:
            return Response(
                {
                    "error": "You do not have permission to view expiry alerts."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        alerts = []

        for certificate in queryset:
            days_remaining = (
                certificate.valid_until - today
            ).days

            if days_remaining < 0:
                expiry_status = "EXPIRED"

                # Keep database status synchronized.
                if certificate.status == Certificate.Status.VALID:
                    certificate.status = Certificate.Status.EXPIRED
                    certificate.save(
                        update_fields=["status"]
                    )

            elif days_remaining <= 30:
                expiry_status = "EXPIRING_SOON"

            else:
                expiry_status = "VALID"

            alerts.append(
                {
                    "certificate_id": certificate.id,
                    "certificate_number": certificate.certificate_number,

                    "instrument": {
                        "id": certificate.instrument.id,
                        "name": certificate.instrument.name,
                        "serial_number": (
                            certificate.instrument.serial_number
                        ),
                    },

                    "owner": {
                        "id": certificate.owner.id,
                        "username": certificate.owner.username,
                    },

                    "issue_date": certificate.issue_date,
                    "valid_until": certificate.valid_until,
                    "days_remaining": days_remaining,

                    "expiry_status": expiry_status,
                    "certificate_status": certificate.status,
                }
            )

        return Response(
            {
                "today": today,
                "total_certificates": len(alerts),

                "expired": sum(
                    1
                    for alert in alerts
                    if alert["expiry_status"] == "EXPIRED"
                ),

                "expiring_soon": sum(
                    1
                    for alert in alerts
                    if alert["expiry_status"] == "EXPIRING_SOON"
                ),

                "valid": sum(
                    1
                    for alert in alerts
                    if alert["expiry_status"] == "VALID"
                ),

                "alerts": alerts,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# PUBLIC - CERTIFICATE VERIFICATION
# ============================================================

class PublicCertificateVerificationView(APIView):
    """
    Public endpoint for verifying a certificate.

    No login is required.
    Anyone with a valid certificate number can check it.
    """

    permission_classes = []

    def get(self, request, certificate_number):
        try:
            certificate = (
                Certificate.objects
                .select_related(
                    "application",
                    "instrument",
                    "owner",
                    "issued_by",
                )
                .get(
                    certificate_number=certificate_number
                )
            )
        except Certificate.DoesNotExist:
            return Response(
                {
                    "valid": False,
                    "message": "Certificate not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Automatically determine whether certificate has expired
        if (
            certificate.status == Certificate.Status.VALID
            and certificate.valid_until < date.today()
        ):
            certificate.status = Certificate.Status.EXPIRED
            certificate.save(
                update_fields=["status"]
            )

        return Response(
            {
                "valid": certificate.status == Certificate.Status.VALID,
                "certificate": {
                    "certificate_number":
                        certificate.certificate_number,

                    "status":
                        certificate.status,

                    "issue_date":
                        certificate.issue_date,

                    "valid_until":
                        certificate.valid_until,

                    "instrument": {
                        "name":
                            certificate.instrument.name,

                        "instrument_type":
                            certificate.instrument.instrument_type,

                        "manufacturer":
                            certificate.instrument.manufacturer,

                        "model_number":
                            certificate.instrument.model_number,

                        "serial_number":
                            certificate.instrument.serial_number,
                    },

                    "owner": {
                        "username":
                            certificate.owner.username,
                    },

                    "application_number":
                        certificate.application.application_number,

                    "issued_by": {
                        "username":
                            certificate.issued_by.username,

                        "role":
                            certificate.issued_by.role,
                    },

                    "remarks":
                        certificate.remarks,
                },
            },
            status=status.HTTP_200_OK,
        )


class PublicInstrumentVerificationView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicInstrumentVerificationSerializer
    lookup_field = "instrument_uid"

    def get_queryset(self):
        return (
            Instrument.objects
            .prefetch_related(
                "certificates__application",
            )
            .all()
        )


# ============================================================
# PUBLIC - CERTIFICATE QR CODE
# ============================================================

class CertificateQRCodeView(APIView):
    """
    Generate a QR code for a certificate.

    The QR code contains the public certificate
    verification API URL.
    """

    permission_classes = []

    def get(self, request, certificate_number):
        try:
            certificate = Certificate.objects.get(
                certificate_number=certificate_number
            )
        except Certificate.DoesNotExist:
            return Response(
                {
                    "valid": False,
                    "message": "Certificate not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Public verification URL
        verification_url = request.build_absolute_uri(
            f"/api/verification/public/certificates/"
            f"{certificate.certificate_number}/"
        )

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
        )

        qr.add_data(verification_url)
        qr.make(fit=True)

        qr_image = qr.make_image()

        # Store image in memory
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        buffer.seek(0)

        return HttpResponse(
            buffer.getvalue(),
            content_type="image/png",
        )


class InstrumentQRCodeView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, instrument_uid):
        instrument = get_object_or_404(
            Instrument,
            instrument_uid=instrument_uid,
        )

        verification_url = (
            f"{request.scheme}://{request.get_host()}"
            f"/api/verification/public/instruments/{instrument.instrument_uid}/"
        )

        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)

        qr_image = qr.make_image()

        response = HttpResponse(
            content_type="image/png",
        )
        qr_image.save(response, format="PNG")

        return response


# ============================================================
# ROLE-BASED DASHBOARD
# ============================================================

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # ====================================================
        # OWNER DASHBOARD
        # ====================================================

        if user.role == "OWNER":

            total_instruments = Instrument.objects.filter(
                owner=user
            ).count()

            total_applications = VerificationApplication.objects.filter(
                applicant=user
            ).count()

            pending_applications = VerificationApplication.objects.filter(
                applicant=user,
                status__in=[
                    VerificationApplication.Status.SUBMITTED,
                    VerificationApplication.Status.UNDER_REVIEW,
                    VerificationApplication.Status.ASSIGNED,
                ],
            ).count()

            under_inspection = VerificationApplication.objects.filter(
                applicant=user,
                status=VerificationApplication.Status.INSPECTION,
            ).count()

            approved = VerificationApplication.objects.filter(
                applicant=user,
                status=VerificationApplication.Status.APPROVED,
            ).count()

            rejected = VerificationApplication.objects.filter(
                applicant=user,
                status=VerificationApplication.Status.REJECTED,
            ).count()

            certificates = Certificate.objects.filter(
                owner=user
            ).count()

            return Response(
                {
                    "role": "OWNER",
                    "dashboard": {
                        "total_instruments":
                            total_instruments,

                        "total_applications":
                            total_applications,

                        "pending_applications":
                            pending_applications,

                        "under_inspection":
                            under_inspection,

                        "approved":
                            approved,

                        "rejected":
                            rejected,

                        "certificates":
                            certificates,
                    },
                },
                status=status.HTTP_200_OK,
            )

        # ====================================================
        # LMO / ADMIN DASHBOARD
        # ====================================================

        if user.role in ["LMO", "ADMIN"]:

            total_applications = (
                VerificationApplication.objects.count()
            )

            pending_review = (
                VerificationApplication.objects.filter(
                    status__in=[
                        VerificationApplication.Status.SUBMITTED,
                        VerificationApplication.Status.UNDER_REVIEW,
                    ]
                ).count()
            )

            assigned = (
                VerificationApplication.objects.filter(
                    status=VerificationApplication.Status.ASSIGNED
                ).count()
            )

            under_inspection = (
                VerificationApplication.objects.filter(
                    status=VerificationApplication.Status.INSPECTION
                ).count()
            )

            approved = (
                VerificationApplication.objects.filter(
                    status=VerificationApplication.Status.APPROVED
                ).count()
            )

            rejected = (
                VerificationApplication.objects.filter(
                    status=VerificationApplication.Status.REJECTED
                ).count()
            )

            certificates = Certificate.objects.count()

            return Response(
                {
                    "role": user.role,
                    "dashboard": {
                        "total_applications":
                            total_applications,

                        "pending_review":
                            pending_review,

                        "assigned":
                            assigned,

                        "under_inspection":
                            under_inspection,

                        "approved":
                            approved,

                        "rejected":
                            rejected,

                        "certificates":
                            certificates,
                    },
                },
                status=status.HTTP_200_OK,
            )

        # ====================================================
        # GATC DASHBOARD
        # ====================================================

        if user.role == "GATC":

            assigned_applications = (
                VerificationApplication.objects.filter(
                    assigned_to=user
                ).count()
            )

            pending_inspections = (
                VerificationApplication.objects.filter(
                    assigned_to=user,
                    status=VerificationApplication.Status.ASSIGNED,
                ).count()
            )

            under_inspection = (
                VerificationApplication.objects.filter(
                    assigned_to=user,
                    status=VerificationApplication.Status.INSPECTION,
                ).count()
            )

            completed_inspections = (
                Inspection.objects.filter(
                    inspector=user
                ).count()
            )

            passed_inspections = (
                Inspection.objects.filter(
                    inspector=user,
                    result=Inspection.Result.PASSED,
                ).count()
            )

            failed_inspections = (
                Inspection.objects.filter(
                    inspector=user,
                    result=Inspection.Result.FAILED,
                ).count()
            )

            return Response(
                {
                    "role": "GATC",
                    "dashboard": {
                        "assigned_applications":
                            assigned_applications,

                        "pending_inspections":
                            pending_inspections,

                        "under_inspection":
                            under_inspection,

                        "completed_inspections":
                            completed_inspections,

                        "passed_inspections":
                            passed_inspections,

                        "failed_inspections":
                            failed_inspections,
                    },
                },
                status=status.HTTP_200_OK,
            )

        # ====================================================
        # UNKNOWN ROLE
        # ====================================================

        return Response(
            {
                "error": "Unsupported user role."
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class VerificationDocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerificationDocumentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user

        queryset = (
            VerificationDocument.objects
            .select_related(
                "application",
                "instrument",
                "uploaded_by",
            )
            .order_by("-uploaded_at")
        )

        if user.role == "OWNER":
            queryset = queryset.filter(
                models.Q(
                    instrument__owner=user
                )
                |
                models.Q(
                    application__applicant=user
                )
            )

        elif user.role == "GATC":
            queryset = queryset.filter(
                application__assigned_to=user
            )

        elif user.role in ["LMO", "ADMIN"]:
            pass

        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        application_id = self.request.data.get("application")
        instrument_id = self.request.data.get("instrument")

        application = None
        instrument = None

        if application_id:
            application = get_object_or_404(
                VerificationApplication,
                id=application_id,
            )

        if instrument_id:
            instrument = get_object_or_404(
                Instrument,
                id=instrument_id,
            )

        # OWNER
        if user.role == "OWNER":
            if application and application.applicant != user:
                raise PermissionDenied(
                    "You cannot upload documents to this application."
                )

            if instrument and instrument.owner != user:
                raise PermissionDenied(
                    "You cannot upload documents to this instrument."
                )

        # GATC
        elif user.role == "GATC":
            if not application:
                raise ValidationError(
                    "GATC uploads must be linked to an application."
                )

            if application.assigned_to != user:
                raise PermissionDenied(
                    "This application is not assigned to you."
                )

        elif user.role not in ["LMO", "ADMIN"]:
            raise PermissionDenied(
                "You do not have permission to upload documents."
            )

        if not application and not instrument:
            raise ValidationError(
                "Provide either an application or an instrument."
            )

        serializer.save(
            uploaded_by=user,
            application=application,
            instrument=instrument,
        )


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response(
                {
                    "error": "Search query 'q' is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        instruments = Instrument.objects.select_related("owner")

        applications = VerificationApplication.objects.select_related(
            "instrument",
            "applicant",
            "assigned_to",
        )

        certificates = Certificate.objects.select_related(
            "instrument",
            "owner",
            "application",
        )

        # -----------------------------
        # ROLE BASED FILTERING
        # -----------------------------

        if user.role == "OWNER":
            instruments = instruments.filter(owner=user)
            applications = applications.filter(applicant=user)
            certificates = certificates.filter(owner=user)

        elif user.role == "GATC":
            applications = applications.filter(assigned_to=user)

            instrument_ids = applications.values_list(
                "instrument_id",
                flat=True,
            )

            certificate_ids = certificates.filter(
                instrument_id__in=instrument_ids
            ).values_list("id", flat=True)

            instruments = instruments.filter(
                id__in=instrument_ids
            )

            certificates = certificates.filter(
                id__in=certificate_ids
            )

        elif user.role in ["LMO", "ADMIN"]:
            pass

        else:
            return Response(
                {
                    "error": "You do not have permission to search."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # -----------------------------
        # SEARCH
        # -----------------------------

        search_filter = (
            models.Q(name__icontains=query)
            | models.Q(instrument_type__icontains=query)
            | models.Q(serial_number__icontains=query)
            | models.Q(instrument_uid__icontains=query)
            | models.Q(owner__username__icontains=query)
        )

        instrument_results = instruments.filter(
            search_filter
        ).distinct()[:20]

        application_filter = (
            models.Q(application_number__icontains=query)
            | models.Q(instrument__name__icontains=query)
            | models.Q(instrument__serial_number__icontains=query)
            | models.Q(applicant__username__icontains=query)
        )

        application_results = applications.filter(
            application_filter
        ).distinct()[:20]

        certificate_filter = (
            models.Q(certificate_number__icontains=query)
            | models.Q(instrument__name__icontains=query)
            | models.Q(instrument__serial_number__icontains=query)
            | models.Q(owner__username__icontains=query)
        )

        certificate_results = certificates.filter(
            certificate_filter
        ).distinct()[:20]

        return Response(
            {
                "query": query,

                "instruments": [
                    {
                        "id": instrument.id,
                        "instrument_uid": instrument.instrument_uid,
                        "name": instrument.name,
                        "instrument_type": instrument.instrument_type,
                        "serial_number": instrument.serial_number,
                        "owner": instrument.owner.username,
                        "status": instrument.status,
                    }
                    for instrument in instrument_results
                ],

                "applications": [
                    {
                        "id": application.id,
                        "application_number": application.application_number,
                        "instrument": application.instrument.name,
                        "serial_number": application.instrument.serial_number,
                        "applicant": application.applicant.username,
                        "status": application.status,
                        "application_type": application.application_type,
                    }
                    for application in application_results
                ],

                "certificates": [
                    {
                        "id": certificate.id,
                        "certificate_number": certificate.certificate_number,
                        "instrument": certificate.instrument.name,
                        "serial_number": certificate.instrument.serial_number,
                        "owner": certificate.owner.username,
                        "issue_date": certificate.issue_date,
                        "valid_until": certificate.valid_until,
                        "status": certificate.status,
                    }
                    for certificate in certificate_results
                ],
            },
            status=status.HTTP_200_OK,
        )