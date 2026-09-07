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

    application_number = models.CharField(
        max_length=50,
        unique=True,
    )

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