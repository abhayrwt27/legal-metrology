from rest_framework import serializers

from .models import VerificationApplication


class VerificationApplicationSerializer(serializers.ModelSerializer):
    instrument_name = serializers.CharField(
        source="instrument.name",
        read_only=True,
    )

    instrument_serial_number = serializers.CharField(
        source="instrument.serial_number",
        read_only=True,
    )

    applicant = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    class Meta:
        model = VerificationApplication

        fields = [
            "id",
            "application_number",
            "instrument",
            "instrument_name",
            "instrument_serial_number",
            "applicant",
            "status",
            "remarks",
            "submitted_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "application_number",
            "applicant",
            "status",
            "submitted_at",
            "updated_at",
        ]