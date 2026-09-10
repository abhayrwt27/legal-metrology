from django.conf import settings
from django.db import models

from instruments.models import Instrument


class VerificationApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        ASSIGNED = "ASSIGNED", "Assigned"
        SCHEDULED = "SCHEDULED", "Scheduled"
        INSPECTION = "INSPECTION", "Inspection"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class ApplicationType(models.TextChoices):
        INITIAL = "INITIAL", "Initial Verification"
        RE_VERIFICATION = "RE_VERIFICATION", "Re-verification"
        RENEWAL = "RENEWAL", "Renewal"

    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="verification_applications",
    )

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_applications",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_verification_applications",
    )

    application_number = models.CharField(
        max_length=50,
        unique=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )

    application_type = models.CharField(
        max_length=20,
        choices=ApplicationType.choices,
        default=ApplicationType.INITIAL,
    )

    previous_application = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="renewal_applications",
    )

    remarks = models.TextField(
        blank=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return self.application_number


class VerificationSchedule(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    application = models.ForeignKey(
        VerificationApplication,
        on_delete=models.CASCADE,
        related_name="schedules",
    )

    scheduled_date = models.DateField()

    scheduled_time = models.TimeField()

    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_verification_schedules",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["scheduled_date", "scheduled_time"]

    def __str__(self):
        return (
            f"{self.application.application_number} - "
            f"{self.scheduled_date} {self.scheduled_time}"
        )


class Inspection(models.Model):
    class Result(models.TextChoices):
        PASSED = "PASSED", "Passed"
        FAILED = "FAILED", "Failed"

    application = models.OneToOneField(
        VerificationApplication,
        on_delete=models.CASCADE,
        related_name="inspection",
    )

    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inspections",
    )

    inspection_date = models.DateField()

    measurements = models.JSONField(
        default=dict,
    )

    result = models.CharField(
        max_length=10,
        choices=Result.choices,
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-inspection_date", "-created_at"]

    def __str__(self):
        return (
            f"{self.application.application_number} - "
            f"{self.result}"
        )


class Certificate(models.Model):
    class Status(models.TextChoices):
        VALID = "VALID", "Valid"
        REVOKED = "REVOKED", "Revoked"
        EXPIRED = "EXPIRED", "Expired"

    application = models.OneToOneField(
        VerificationApplication,
        on_delete=models.PROTECT,
        related_name="certificate",
    )

    certificate_number = models.CharField(
        max_length=50,
        unique=True,
    )

    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.PROTECT,
        related_name="certificates",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="certificates",
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issued_certificates",
    )

    issue_date = models.DateField()

    valid_until = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.VALID,
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-issue_date", "-created_at"]

    def __str__(self):
        return self.certificate_number


class VerificationDocument(models.Model):
    class DocumentType(models.TextChoices):
        INSTRUMENT_PHOTO = "INSTRUMENT_PHOTO", "Instrument Photo"
        VERIFICATION_DOCUMENT = "VERIFICATION_DOCUMENT", "Verification Document"
        INSPECTION_PHOTO = "INSPECTION_PHOTO", "Inspection Photo"
        OTHER = "OTHER", "Other"

    application = models.ForeignKey(
        VerificationApplication,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )

    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_verification_documents",
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
    )

    file = models.FileField(
        upload_to="verification_documents/%Y/%m/",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.file.name
