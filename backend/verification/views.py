import os
import io
import uuid
from datetime import timedelta

import qrcode
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from instruments.models import Instrument

from .models import (
    Certificate,
    Inspection,
    VerificationApplication,
    VerificationDocument,
    VerificationSchedule,
)
from .permissions import IsGATC, IsLMOOrAdmin
from .serializers import (
    CertificateSerializer,
    InspectionSerializer,
    VerificationApplicationSerializer,
    VerificationDocumentSerializer,
    VerificationScheduleSerializer,
)


# =============================================================================
# HELPERS
# =============================================================================


def generate_application_number():
    last_application = (
        VerificationApplication.objects
        .order_by("-id")
        .first()
    )

    if not last_application:
        number = 1
    else:
        try:
            number = int(
                last_application.application_number.split("-")[-1]
            ) + 1
        except (ValueError, IndexError):
            number = last_application.id + 1

    return f"VAPP-{number:06d}"


def generate_certificate_number():
    last_certificate = (
        Certificate.objects
        .order_by("-id")
        .first()
    )

    if not last_certificate:
        number = 1
    else:
        try:
            number = int(
                last_certificate.certificate_number.split("-")[-1]
            ) + 1
        except (ValueError, IndexError):
            number = last_certificate.id + 1

    return f"CERT-{number:06d}"


def update_expired_certificates():
    today = timezone.localdate()

    Certificate.objects.filter(
        status=Certificate.Status.VALID,
        valid_until__lt=today,
    ).update(
        status=Certificate.Status.EXPIRED
    )


def get_instrument_from_uid(instrument_uid):
    try:
        return Instrument.objects.get(
            instrument_uid=instrument_uid
        )
    except (Instrument.DoesNotExist, ValueError):
        raise Http404("Instrument not found.")


def public_instrument_data(instrument):
    update_expired_certificates()

    certificates = (
        Certificate.objects
        .filter(instrument=instrument)
        .order_by("-issue_date", "-created_at")
    )

    current_certificate = (
        certificates
        .filter(status=Certificate.Status.VALID)
        .order_by("-issue_date")
        .first()
    )

    applications = (
        VerificationApplication.objects
        .filter(instrument=instrument)
        .select_related("assigned_to")
        .prefetch_related("inspection")
        .order_by("-submitted_at")
    )

    history = []

    for application in applications:
        inspection_data = None

        try:
            inspection = application.inspection
            inspection_data = {
                "inspection_date": inspection.inspection_date,
                "result": inspection.result,
                "remarks": inspection.remarks,
            }
        except Inspection.DoesNotExist:
            pass

        certificate_data = None

        try:
            certificate = application.certificate
            certificate_data = {
                "certificate_number": certificate.certificate_number,
                "issue_date": certificate.issue_date,
                "valid_until": certificate.valid_until,
                "status": certificate.status,
            }
        except Certificate.DoesNotExist:
            pass

        history.append(
            {
                "application_number": application.application_number,
                "application_type": application.application_type,
                "status": application.status,
                "submitted_at": application.submitted_at,
                "inspection": inspection_data,
                "certificate": certificate_data,
            }
        )

    return {
        "instrument": {
            "id": instrument.id,
            "instrument_uid": str(instrument.instrument_uid),
            "name": instrument.name,
            "instrument_type": instrument.instrument_type,
            "manufacturer": instrument.manufacturer,
            "model_number": instrument.model_number,
            "serial_number": instrument.serial_number,
            "capacity": instrument.capacity,
            "accuracy": instrument.accuracy,
            "location": instrument.location,
            "purchase_date": instrument.purchase_date,
            "description": instrument.description,
            "status": instrument.status,
        },
        "current_certificate": (
            CertificateSerializer(current_certificate).data
            if current_certificate
            else None
        ),
        "certificates": CertificateSerializer(
            certificates,
            many=True,
        ).data,
        "verification_history": history,
    }


# =============================================================================
# OWNER APPLICATIONS
# =============================================================================


class VerificationApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.OWNER:
            return Response(
                {
                    "error": "Only instrument owners can access this endpoint."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        applications = (
            VerificationApplication.objects
            .filter(applicant=request.user)
            .select_related(
                "instrument",
                "assigned_to",
            )
            .order_by("-submitted_at")
        )

        return Response(
            VerificationApplicationSerializer(
                applications,
                many=True,
            ).data
        )

    @transaction.atomic
    def post(self, request):
        if request.user.role != User.Role.OWNER:
            return Response(
                {
                    "error": "Only instrument owners can submit applications."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        instrument_id = request.data.get("instrument")
        application_type = request.data.get(
            "application_type",
            VerificationApplication.ApplicationType.INITIAL,
        )
        previous_application_id = request.data.get(
            "previous_application"
        )
        remarks = request.data.get("remarks", "")

        try:
            instrument = Instrument.objects.get(
                id=instrument_id,
                owner=request.user,
            )
        except Instrument.DoesNotExist:
            return Response(
                {
                    "error": "Instrument not found or not owned by you."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        valid_types = {
            choice[0]
            for choice in VerificationApplication.ApplicationType.choices
        }

        if application_type not in valid_types:
            return Response(
                {
                    "error": "Invalid application type."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_application = None

        if application_type in [
            VerificationApplication.ApplicationType.RE_VERIFICATION,
            VerificationApplication.ApplicationType.RENEWAL,
        ]:
            if not previous_application_id:
                return Response(
                    {
                        "error": (
                            "previous_application is required for "
                            "re-verification or renewal."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                previous_application = (
                    VerificationApplication.objects
                    .get(
                        id=previous_application_id,
                        instrument=instrument,
                        applicant=request.user,
                        status=VerificationApplication.Status.APPROVED,
                    )
                )
            except VerificationApplication.DoesNotExist:
                return Response(
                    {
                        "error": (
                            "The selected previous application is not a "
                            "valid approved application for this instrument."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        application = VerificationApplication.objects.create(
            instrument=instrument,
            applicant=request.user,
            application_number=generate_application_number(),
            application_type=application_type,
            previous_application=previous_application,
            remarks=remarks,
            status=VerificationApplication.Status.SUBMITTED,
        )

        instrument.status = Instrument.Status.UNDER_VERIFICATION
        instrument.save(update_fields=["status", "updated_at"])

        return Response(
            VerificationApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class VerificationApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return (
                VerificationApplication.objects
                .select_related(
                    "instrument",
                    "applicant",
                    "assigned_to",
                )
                .get(
                    id=pk,
                    applicant=request.user,
                )
            )
        except VerificationApplication.DoesNotExist:
            raise Http404("Application not found.")

    def get(self, request, pk):
        if request.user.role != User.Role.OWNER:
            return Response(
                {
                    "error": "Only instrument owners can access this endpoint."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        application = self.get_object(request, pk)

        return Response(
            VerificationApplicationSerializer(application).data
        )


# =============================================================================
# OFFICER APPLICATIONS
# =============================================================================


class OfficerApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [
            User.Role.LMO,
            User.Role.GATC,
            User.Role.ADMIN,
        ]:
            return Response(
                {
                    "error": "Officer access required."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = (
            VerificationApplication.objects
            .select_related(
                "instrument",
                "applicant",
                "assigned_to",
            )
            .order_by("-submitted_at")
        )

        if request.user.role == User.Role.GATC:
            queryset = queryset.filter(
                assigned_to=request.user
            )

        return Response(
            VerificationApplicationSerializer(
                queryset,
                many=True,
            ).data
        )


class AssignApplicationView(APIView):
    permission_classes = [IsAuthenticated, IsLMOOrAdmin]

    def patch(self, request, pk):
        try:
            application = (
                VerificationApplication.objects
                .select_related("instrument")
                .get(id=pk)
            )
        except VerificationApplication.DoesNotExist:
            return Response(
                {
                    "error": "Application not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        officer_id = request.data.get("officer_id")

        if not officer_id:
            return Response(
                {
                    "error": "officer_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            officer = User.objects.get(
                id=officer_id,
                role=User.Role.GATC,
                is_active=True,
            )
        except User.DoesNotExist:
            return Response(
                {
                    "error": "Valid active GATC not found."
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

        return Response(
            VerificationApplicationSerializer(application).data
        )


# =============================================================================
# SCHEDULING
# =============================================================================


class VerificationScheduleCreateView(APIView):
    permission_classes = [IsAuthenticated, IsLMOOrAdmin]

    def post(self, request):
        application_id = request.data.get("application")
        scheduled_date = request.data.get("scheduled_date")
        scheduled_time = request.data.get("scheduled_time")
        remarks = request.data.get("remarks", "")

        if not application_id:
            return Response(
                {
                    "error": "application is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not scheduled_date:
            return Response(
                {
                    "error": "scheduled_date is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not scheduled_time:
            return Response(
                {
                    "error": "scheduled_time is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application = VerificationApplication.objects.get(
                id=application_id
            )
        except VerificationApplication.DoesNotExist:
            return Response(
                {
                    "error": "Application not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not application.assigned_to:
            return Response(
                {
                    "error": "Assign the application to a GATC before scheduling."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if application.status not in [
            VerificationApplication.Status.ASSIGNED,
            VerificationApplication.Status.SCHEDULED,
        ]:
            return Response(
                {
                    "error": (
                        "Only assigned applications can be scheduled."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule = VerificationSchedule.objects.create(
            application=application,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            scheduled_by=request.user,
            status=VerificationSchedule.Status.SCHEDULED,
            remarks=remarks,
        )

        application.status = VerificationApplication.Status.SCHEDULED
        application.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            VerificationScheduleSerializer(schedule).data,
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# INSPECTION
# =============================================================================


class InspectionCreateView(APIView):
    permission_classes = [IsAuthenticated, IsGATC]

    @transaction.atomic
    def post(self, request):
        application_id = request.data.get("application")
        inspection_date = request.data.get("inspection_date")
        measurements = request.data.get("measurements", {})
        result = request.data.get("result")
        remarks = request.data.get("remarks", "")

        if not application_id:
            return Response(
                {
                    "error": "application is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application = (
                VerificationApplication.objects
                .select_related("instrument", "assigned_to")
                .get(
                    id=application_id,
                    assigned_to=request.user,
                )
            )
        except VerificationApplication.DoesNotExist:
            return Response(
                {
                    "error": "Assigned application not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.status not in [
            VerificationApplication.Status.ASSIGNED,
            VerificationApplication.Status.SCHEDULED,
            VerificationApplication.Status.INSPECTION,
        ]:
            return Response(
                {
                    "error": "This application is not ready for inspection."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not inspection_date:
            return Response(
                {
                    "error": "inspection_date is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if result not in [
            Inspection.Result.PASSED,
            Inspection.Result.FAILED,
        ]:
            return Response(
                {
                    "error": "Result must be PASSED or FAILED."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(measurements, dict):
            return Response(
                {
                    "error": "measurements must be a JSON object."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(application, "inspection"):
            return Response(
                {
                    "error": "An inspection has already been recorded."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        inspection = Inspection.objects.create(
            application=application,
            inspector=request.user,
            inspection_date=inspection_date,
            measurements=measurements,
            result=result,
            remarks=remarks,
        )

        application.status = VerificationApplication.Status.INSPECTION
        application.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        if result == Inspection.Result.FAILED:
            application.instrument.status = Instrument.Status.REJECTED
            application.instrument.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return Response(
            InspectionSerializer(inspection).data,
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# APPROVAL / REJECTION
# =============================================================================


class ApplicationDecisionView(APIView):
    permission_classes = [IsAuthenticated, IsLMOOrAdmin]

    @transaction.atomic
    def patch(self, request, pk):
        decision = request.data.get("decision")
        remarks = request.data.get("remarks", "")

        if decision not in [
            VerificationApplication.Status.APPROVED,
            VerificationApplication.Status.REJECTED,
        ]:
            return Response(
                {
                    "error": "Decision must be APPROVED or REJECTED."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application = (
                VerificationApplication.objects
                .select_related("instrument", "applicant")
                .get(id=pk)
            )
        except VerificationApplication.DoesNotExist:
            return Response(
                {
                    "error": "Application not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.status not in [
            VerificationApplication.Status.INSPECTION,
            VerificationApplication.Status.ASSIGNED,
        ]:
            return Response(
                {
                    "error": (
                        "Only applications in inspection or assigned "
                        "status can receive a decision."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        inspection = None

        try:
            inspection = application.inspection
        except Inspection.DoesNotExist:
            pass

        if decision == VerificationApplication.Status.APPROVED:
            if not inspection:
                return Response(
                    {
                        "error": (
                            "An inspection must be recorded before approval."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if inspection.result != Inspection.Result.PASSED:
                return Response(
                    {
                        "error": (
                            "An application cannot be approved because "
                            "the inspection result is FAILED."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            today = timezone.localdate()

            application.status = VerificationApplication.Status.APPROVED
            application.remarks = remarks or application.remarks
            application.save(
                update_fields=[
                    "status",
                    "remarks",
                    "updated_at",
                ]
            )

            existing_certificate = None

            try:
                existing_certificate = application.certificate
            except Certificate.DoesNotExist:
                pass

            if existing_certificate:
                certificate = existing_certificate
            else:
                certificate = Certificate.objects.create(
                    application=application,
                    certificate_number=generate_certificate_number(),
                    instrument=application.instrument,
                    owner=application.applicant,
                    issued_by=request.user,
                    issue_date=today,
                    valid_until=today + timedelta(days=365),
                    status=Certificate.Status.VALID,
                    remarks=remarks,
                )

            application.instrument.status = Instrument.Status.VERIFIED
            application.instrument.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "application": VerificationApplicationSerializer(
                        application
                    ).data,
                    "certificate": CertificateSerializer(
                        certificate
                    ).data,
                }
            )

        application.status = VerificationApplication.Status.REJECTED
        application.remarks = remarks or application.remarks
        application.save(
            update_fields=[
                "status",
                "remarks",
                "updated_at",
            ]
        )

        application.instrument.status = Instrument.Status.REJECTED
        application.instrument.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            VerificationApplicationSerializer(application).data
        )


# =============================================================================
# CERTIFICATES
# =============================================================================


class CertificateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        update_expired_certificates()

        queryset = (
            Certificate.objects
            .select_related(
                "instrument",
                "owner",
                "issued_by",
                "application",
            )
            .order_by("-issue_date", "-created_at")
        )

        if request.user.role == User.Role.OWNER:
            queryset = queryset.filter(
                owner=request.user
            )

        elif request.user.role == User.Role.GATC:
            queryset = queryset.filter(
                application__assigned_to=request.user
            )

        elif request.user.role not in [
            User.Role.LMO,
            User.Role.ADMIN,
        ]:
            return Response(
                {
                    "error": "You do not have permission to view certificates."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            CertificateSerializer(
                queryset,
                many=True,
            ).data
        )


class CertificateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        update_expired_certificates()

        try:
            certificate = (
                Certificate.objects
                .select_related(
                    "instrument",
                    "owner",
                    "issued_by",
                    "application",
                )
                .get(id=pk)
            )
        except Certificate.DoesNotExist:
            return Response(
                {
                    "error": "Certificate not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == User.Role.OWNER:
            if certificate.owner_id != request.user.id:
                return Response(
                    {
                        "error": "You do not have access to this certificate."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        elif request.user.role == User.Role.GATC:
            if certificate.application.assigned_to_id != request.user.id:
                return Response(
                    {
                        "error": "You do not have access to this certificate."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        elif request.user.role not in [
            User.Role.LMO,
            User.Role.ADMIN,
        ]:
            return Response(
                {
                    "error": "You do not have permission to view this certificate."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            CertificateSerializer(certificate).data
        )


# =============================================================================
# DASHBOARD
# =============================================================================


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        update_expired_certificates()

        user = request.user

        if user.role == User.Role.OWNER:
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
                    VerificationApplication.Status.SCHEDULED,
                    VerificationApplication.Status.INSPECTION,
                ],
            ).count()

            certificates = Certificate.objects.filter(
                owner=user
            ).count()

            return Response(
                {
                    "username": user.username,
                    "role": user.role,
                    "dashboard": {
                        "total_instruments": total_instruments,
                        "total_applications": total_applications,
                        "pending_applications": pending_applications,
                        "certificates": certificates,
                    },
                }
            )

        if user.role == User.Role.GATC:
            assigned_applications = VerificationApplication.objects.filter(
                assigned_to=user
            ).count()

            pending_inspections = VerificationApplication.objects.filter(
                assigned_to=user,
                status__in=[
                    VerificationApplication.Status.ASSIGNED,
                    VerificationApplication.Status.SCHEDULED,
                ],
            ).count()

            under_inspection = VerificationApplication.objects.filter(
                assigned_to=user,
                status=VerificationApplication.Status.INSPECTION,
            ).count()

            completed_inspections = Inspection.objects.filter(
                inspector=user
            ).count()

            return Response(
                {
                    "username": user.username,
                    "role": user.role,
                    "dashboard": {
                        "assigned_applications": assigned_applications,
                        "pending_inspections": pending_inspections,
                        "under_inspection": under_inspection,
                        "completed_inspections": completed_inspections,
                    },
                }
            )

        total_applications = VerificationApplication.objects.count()

        pending_review = VerificationApplication.objects.filter(
            status__in=[
                VerificationApplication.Status.SUBMITTED,
                VerificationApplication.Status.UNDER_REVIEW,
            ]
        ).count()

        assigned = VerificationApplication.objects.filter(
            status=VerificationApplication.Status.ASSIGNED
        ).count()

        under_inspection = VerificationApplication.objects.filter(
            status__in=[
                VerificationApplication.Status.SCHEDULED,
                VerificationApplication.Status.INSPECTION,
            ]
        ).count()

        return Response(
            {
                "username": user.username,
                "role": user.role,
                "dashboard": {
                    "total_applications": total_applications,
                    "pending_review": pending_review,
                    "assigned": assigned,
                    "under_inspection": under_inspection,
                },
            }
        )


# =============================================================================
# PUBLIC INSTRUMENT VERIFICATION
# =============================================================================


class PublicInstrumentVerificationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, instrument_uid):
        instrument = get_instrument_from_uid(
            instrument_uid
        )

        return Response(
            public_instrument_data(instrument)
        )


class PublicInstrumentQRView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, instrument_uid):
        instrument = get_instrument_from_uid(
            instrument_uid
        )

        # In production, set PUBLIC_FRONTEND_URL to the deployed
        # frontend URL. For local development the API URL is used.
        frontend_url = os.getenv(
            "PUBLIC_FRONTEND_URL",
            "",
        ).rstrip("/")

        if frontend_url:
            verification_url = (
                f"{frontend_url}/verify/"
                f"{instrument.instrument_uid}/"
            )
        else:
            verification_url = (
                f"{request.scheme}://{request.get_host()}"
                f"/api/verification/public/instruments/"
                f"{instrument.instrument_uid}/"
            )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )

        qr.add_data(verification_url)
        qr.make(fit=True)

        image = qr.make_image()

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return FileResponse(
            buffer,
            content_type="image/png",
        )


# =============================================================================
# PUBLIC CERTIFICATE VERIFICATION
# =============================================================================


class PublicCertificateVerificationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, certificate_number):
        update_expired_certificates()

        try:
            certificate = (
                Certificate.objects
                .select_related(
                    "instrument",
                    "owner",
                    "issued_by",
                    "application",
                )
                .get(
                    certificate_number=certificate_number
                )
            )
        except Certificate.DoesNotExist:
            return Response(
                {
                    "verified": False,
                    "error": "Certificate not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "verified": certificate.status
                == Certificate.Status.VALID,
                "certificate": CertificateSerializer(
                    certificate
                ).data,
            }
        )


class PublicCertificateQRView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, certificate_number):
        try:
            certificate = Certificate.objects.get(
                certificate_number=certificate_number
            )
        except Certificate.DoesNotExist:
            raise Http404("Certificate not found.")

        frontend_url = os.getenv(
            "PUBLIC_FRONTEND_URL",
            "",
        ).rstrip("/")

        if frontend_url:
            verification_url = (
                f"{frontend_url}/verify/certificate/"
                f"{certificate.certificate_number}/"
            )
        else:
            verification_url = (
                f"{request.scheme}://{request.get_host()}"
                f"/api/verification/public/certificates/"
                f"{certificate.certificate_number}/"
            )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )

        qr.add_data(verification_url)
        qr.make(fit=True)

        image = qr.make_image()

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return FileResponse(
            buffer,
            content_type="image/png",
        )


# =============================================================================
# EXPIRY ALERTS
# =============================================================================


class CertificateExpiryAlertView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        update_expired_certificates()

        today = timezone.localdate()
        alert_date = today + timedelta(days=30)

        queryset = (
            Certificate.objects
            .select_related(
                "instrument",
                "owner",
            )
            .filter(
                valid_until__lte=alert_date,
            )
            .order_by("valid_until")
        )

        if request.user.role == User.Role.OWNER:
            queryset = queryset.filter(
                owner=request.user
            )

        elif request.user.role not in [
            User.Role.LMO,
            User.Role.ADMIN,
        ]:
            return Response(
                {
                    "error": "You do not have permission to view expiry alerts."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        alerts = []

        for certificate in queryset:
            if certificate.valid_until < today:
                alert_type = "EXPIRED"
            else:
                days_remaining = (
                    certificate.valid_until - today
                ).days

                if days_remaining <= 7:
                    alert_type = "EXPIRING_SOON"
                else:
                    alert_type = "UPCOMING_EXPIRY"

            alerts.append(
                {
                    "certificate_number": certificate.certificate_number,
                    "instrument_name": certificate.instrument.name,
                    "serial_number": certificate.instrument.serial_number,
                    "valid_until": certificate.valid_until,
                    "status": certificate.status,
                    "alert_type": alert_type,
                }
            )

        return Response(alerts)


# =============================================================================
# SEARCH
# =============================================================================


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get(
            "q",
            "",
        ).strip()

        if not query:
            return Response(
                {
                    "query": "",
                    "instruments": [],
                    "applications": [],
                    "certificates": [],
                }
            )

        instruments = Instrument.objects.filter(
            Q(name__icontains=query)
            | Q(instrument_type__icontains=query)
            | Q(manufacturer__icontains=query)
            | Q(model_number__icontains=query)
            | Q(serial_number__icontains=query)
            | Q(location__icontains=query)
        )

        applications = VerificationApplication.objects.filter(
            Q(application_number__icontains=query)
            | Q(instrument__name__icontains=query)
            | Q(instrument__serial_number__icontains=query)
            | Q(applicant__username__icontains=query)
        ).select_related(
            "instrument",
            "applicant",
            "assigned_to",
        )

        certificates = Certificate.objects.filter(
            Q(certificate_number__icontains=query)
            | Q(instrument__name__icontains=query)
            | Q(instrument__serial_number__icontains=query)
            | Q(owner__username__icontains=query)
        ).select_related(
            "instrument",
            "owner",
            "issued_by",
        )

        if request.user.role == User.Role.OWNER:
            instruments = instruments.filter(
                owner=request.user
            )

            applications = applications.filter(
                applicant=request.user
            )

            certificates = certificates.filter(
                owner=request.user
            )

        elif request.user.role == User.Role.GATC:
            applications = applications.filter(
                assigned_to=request.user
            )

            certificates = certificates.filter(
                application__assigned_to=request.user
            )

            instruments = instruments.filter(
                verification_applications__assigned_to=request.user
            ).distinct()

        elif request.user.role not in [
            User.Role.LMO,
            User.Role.ADMIN,
        ]:
            return Response(
                {
                    "error": "You do not have permission to search records."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "query": query,
                "instruments": [
                    {
                        "id": instrument.id,
                        "instrument_uid": str(
                            instrument.instrument_uid
                        ),
                        "name": instrument.name,
                        "instrument_type": instrument.instrument_type,
                        "manufacturer": instrument.manufacturer,
                        "serial_number": instrument.serial_number,
                        "status": instrument.status,
                    }
                    for instrument in instruments[:50]
                ],
                "applications": [
                    {
                        "id": application.id,
                        "application_number": application.application_number,
                        "instrument_name": application.instrument.name,
                        "serial_number": application.instrument.serial_number,
                        "applicant": application.applicant.username,
                        "status": application.status,
                        "application_type": application.application_type,
                    }
                    for application in applications[:50]
                ],
                "certificates": [
                    {
                        "id": certificate.id,
                        "certificate_number": certificate.certificate_number,
                        "instrument_name": certificate.instrument.name,
                        "serial_number": certificate.instrument.serial_number,
                        "owner": certificate.owner.username,
                        "issue_date": certificate.issue_date,
                        "valid_until": certificate.valid_until,
                        "status": certificate.status,
                    }
                    for certificate in certificates[:50]
                ],
            }
        )


# =============================================================================
# DOCUMENTS
# =============================================================================


class VerificationDocumentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            VerificationDocument.objects
            .select_related(
                "application",
                "instrument",
                "uploaded_by",
            )
            .order_by("-uploaded_at")
        )

        if request.user.role == User.Role.OWNER:
            queryset = queryset.filter(
                Q(instrument__owner=request.user)
                | Q(application__applicant=request.user)
            ).distinct()

        elif request.user.role == User.Role.GATC:
            queryset = queryset.filter(
                Q(application__assigned_to=request.user)
                | Q(instrument__verification_applications__assigned_to=request.user)
            ).distinct()

        elif request.user.role not in [
            User.Role.LMO,
            User.Role.ADMIN,
        ]:
            return Response(
                {
                    "error": "You do not have permission to view documents."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            VerificationDocumentSerializer(
                queryset,
                many=True,
                context={"request": request},
            ).data
        )

    def post(self, request):
        serializer = VerificationDocumentSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        instrument = serializer.validated_data.get(
            "instrument"
        )

        application = serializer.validated_data.get(
            "application"
        )

        if request.user.role == User.Role.OWNER:
            if instrument and instrument.owner_id != request.user.id:
                return Response(
                    {
                        "error": "You can only upload documents for your instruments."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if application and application.applicant_id != request.user.id:
                return Response(
                    {
                        "error": "You can only upload documents for your applications."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        elif request.user.role == User.Role.GATC:
            if application and application.assigned_to_id != request.user.id:
                return Response(
                    {
                        "error": "You can only upload documents for applications assigned to you."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if (
                instrument
                and not VerificationApplication.objects.filter(
                    instrument=instrument,
                    assigned_to=request.user,
                ).exists()
            ):
                return Response(
                    {
                        "error": "You do not have access to this instrument."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        document = serializer.save(
            uploaded_by=request.user
        )

        return Response(
            VerificationDocumentSerializer(
                document,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# PUBLIC CERTIFICATE / INSTRUMENT ROUTING HELPERS
# =============================================================================


class PublicInstrumentLookupView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        uid = request.query_params.get(
            "uid",
            "",
        ).strip()

        if not uid:
            return Response(
                {
                    "error": "uid query parameter is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instrument = get_instrument_from_uid(uid)

        return Response(
            public_instrument_data(instrument)
        )
