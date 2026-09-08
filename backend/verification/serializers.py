from rest_framework import serializers

from .models import Inspection, VerificationApplication


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
    assigned_to = serializers.PrimaryKeyRelatedField(
        read_only=True,
        allow_null=True,
    )
    assigned_to_username = serializers.CharField(
        source="assigned_to.username",
        read_only=True,
        allow_null=True,
    )
    assigned_to_role = serializers.CharField(
        source="assigned_to.role",
        read_only=True,
        allow_null=True,
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
            "assigned_to",
            "assigned_to_username",
            "assigned_to_role",
            "status",
            "remarks",
            "submitted_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "application_number",
            "applicant",
            "assigned_to",
            "assigned_to_username",
            "assigned_to_role",
            "status",
            "submitted_at",
            "updated_at",
        ]


class InspectionSerializer(serializers.ModelSerializer):
    application_number = serializers.CharField(
        source="application.application_number",
        read_only=True,
    )
    inspector_username = serializers.CharField(
        source="inspector.username",
        read_only=True,
    )

    class Meta:
        model = Inspection
        fields = [
            "id",
            "application",
            "application_number",
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
            "created_at",
            "updated_at",
        ]

    def validate_application(self, application):
        user = self.context["request"].user

        if application.assigned_to != user:
            raise serializers.ValidationError(
                "This application is not assigned to you."
            )

        if application.status not in [
            VerificationApplication.Status.ASSIGNED,
            VerificationApplication.Status.INSPECTION,
        ]:
            raise serializers.ValidationError(
                "This application is not available for inspection."
            )

        return application