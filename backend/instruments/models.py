import uuid

from django.conf import settings
from django.db import models


class Instrument(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        UNDER_VERIFICATION = "UNDER_VERIFICATION", "Under Verification"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instruments",
    )

    # Permanent identity of the physical instrument.
    # This value never changes during re-verification/renewal.
    instrument_uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    name = models.CharField(max_length=150)
    instrument_type = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=150, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, unique=True)
    capacity = models.CharField(max_length=100, blank=True)
    accuracy = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.serial_number}"