from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        LMO = "LMO", "Legal Metrology Officer"
        GATC = "GATC", "Government Approved Test Centre"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(
        max_length=5,
        choices=Role.choices,
        default=Role.OWNER,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
