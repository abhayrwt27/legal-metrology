from django.conf import settings
from django.db import models

from instruments.models import Instrument


class VerificationApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        ASSIGNED = "ASSIGNED", "Assigned"
        INSPECTION = "INSPECTION", "Inspection"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

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
    application_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.application_number} - {self.instrument.name}"


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
    measurements = models.JSONField(default=dict)
    result = models.CharField(
        max_length=10,
        choices=Result.choices,
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.certificate_number