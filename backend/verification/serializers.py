from rest_framework import serializers

from .models import (
    Certificate,
    Inspection,
    VerificationApplication,
    VerificationDocument,
    VerificationSchedule,
)


class VerificationApplicationSerializer(serializers.ModelSerializer):
    applicant = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    applicant_username = serializers.CharField(
        source="applicant.username",
        read_only=True,
    )

    assigned_to_username = serializers.CharField(
        source="assigned_to.username",
        read_only=True,
        allow_null=True,
    )

    instrument_name = serializers.CharField(
        source="instrument.name",
        read_only=True,
    )

    instrument_serial_number = serializers.CharField(
        source="instrument.serial_number",
        read_only=True,
    )

    instrument_uid = serializers.UUIDField(
        source="instrument.instrument_uid",
        read_only=True,
    )

    certificate_number = serializers.SerializerMethodField()

    class Meta:
        model = VerificationApplication

        fields = [
            "id",
            "instrument",
            "instrument_name",
            "instrument_serial_number",
            "instrument_uid",
            "applicant",
            "applicant_username",
            "assigned_to",
            "assigned_to_username",
            "application_number",
            "status",
            "application_type",
            "previous_application",
            "remarks",
            "submitted_at",
            "updated_at",
            "certificate_number",
        ]

        read_only_fields = [
            "id",
            "applicant",
            "applicant_username",
            "assigned_to",
            "assigned_to_username",
            "application_number",
            "status",
            "instrument_name",
            "instrument_serial_number",
            "instrument_uid",
            "submitted_at",
            "updated_at",
            "certificate_number",
        ]

    def get_certificate_number(self, obj):
        try:
            return obj.certificate.certificate_number
        except Certificate.DoesNotExist:
            return None


class VerificationScheduleSerializer(serializers.ModelSerializer):
    scheduled_by_username = serializers.CharField(
        source="scheduled_by.username",
        read_only=True,
    )

    application_number = serializers.CharField(
        source="application.application_number",
        read_only=True,
    )

    class Meta:
        model = VerificationSchedule

        fields = [
            "id",
            "application",
            "application_number",
            "scheduled_date",
            "scheduled_time",
            "scheduled_by",
            "scheduled_by_username",
            "status",
            "remarks",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "scheduled_by",
            "scheduled_by_username",
            "application_number",
            "status",
            "created_at",
            "updated_at",
        ]


class InspectionSerializer(serializers.ModelSerializer):
    inspector = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    inspector_username = serializers.CharField(
        source="inspector.username",
        read_only=True,
    )

    application_number = serializers.CharField(
        source="application.application_number",
        read_only=True,
    )

    instrument_name = serializers.CharField(
        source="application.instrument.name",
        read_only=True,
    )

    instrument_serial_number = serializers.CharField(
        source="application.instrument.serial_number",
        read_only=True,
    )

    class Meta:
        model = Inspection

        fields = [
            "id",
            "application",
            "application_number",
            "instrument_name",
            "instrument_serial_number",
            "inspector",
            "inspector_username",
            "inspection_date",
            "measurements",
            "result",
            "remarks",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "inspector",
            "inspector_username",
            "application_number",
            "instrument_name",
            "instrument_serial_number",
            "created_at",
            "updated_at",
        ]


class CertificateSerializer(serializers.ModelSerializer):
    application_number = serializers.CharField(
        source="application.application_number",
        read_only=True,
    )

    instrument_name = serializers.CharField(
        source="instrument.name",
        read_only=True,
    )

    instrument_serial_number = serializers.CharField(
        source="instrument.serial_number",
        read_only=True,
    )

    instrument_uid = serializers.UUIDField(
        source="instrument.instrument_uid",
        read_only=True,
    )

    owner_username = serializers.CharField(
        source="owner.username",
        read_only=True,
    )

    issued_by_username = serializers.CharField(
        source="issued_by.username",
        read_only=True,
    )

    class Meta:
        model = Certificate

        fields = [
            "id",
            "application",
            "application_number",
            "certificate_number",
            "instrument",
            "instrument_name",
            "instrument_serial_number",
            "instrument_uid",
            "owner",
            "owner_username",
            "issued_by",
            "issued_by_username",
            "issue_date",
            "valid_until",
            "status",
            "remarks",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "application",
            "application_number",
            "certificate_number",
            "instrument",
            "instrument_name",
            "instrument_serial_number",
            "instrument_uid",
            "owner",
            "owner_username",
            "issued_by",
            "issued_by_username",
            "issue_date",
            "valid_until",
            "status",
            "created_at",
        ]


class VerificationDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(
        source="uploaded_by.username",
        read_only=True,
    )

    application_number = serializers.CharField(
        source="application.application_number",
        read_only=True,
        allow_null=True,
    )

    instrument_name = serializers.CharField(
        source="instrument.name",
        read_only=True,
        allow_null=True,
    )

    instrument_serial_number = serializers.CharField(
        source="instrument.serial_number",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = VerificationDocument

        fields = [
            "id",
            "application",
            "application_number",
            "instrument",
            "instrument_name",
            "instrument_serial_number",
            "uploaded_by",
            "uploaded_by_username",
            "document_type",
            "file",
            "description",
            "uploaded_at",
        ]

        read_only_fields = [
            "id",
            "uploaded_by",
            "uploaded_by_username",
            "application_number",
            "instrument_name",
            "instrument_serial_number",
            "uploaded_at",
        ]
