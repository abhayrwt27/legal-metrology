from rest_framework import serializers

from .models import (
    Inspection,
    VerificationApplication,
    VerificationSchedule,
    VerificationDocument,
)

from instruments.models import Instrument


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
            "application_type",
            "previous_application",
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

    def validate(self, attrs):
        application_type = attrs.get(
            "application_type",
            VerificationApplication.ApplicationType.INITIAL,
        )
        previous_application = attrs.get("previous_application")
        instrument = attrs.get("instrument")

        if application_type in [
            VerificationApplication.ApplicationType.RE_VERIFICATION,
            VerificationApplication.ApplicationType.RENEWAL,
        ]:
            if previous_application is None:
                raise serializers.ValidationError(
                    {
                        "previous_application": (
                            "Previous application is required for "
                            "re-verification or renewal."
                        )
                    }
                )

            if previous_application.instrument_id != instrument.id:
                raise serializers.ValidationError(
                    {
                        "previous_application": (
                            "Previous application must belong to "
                            "the same instrument."
                        )
                    }
                )

            if previous_application.applicant_id != self.context["request"].user.id:
                raise serializers.ValidationError(
                    {
                        "previous_application": (
                            "Previous application must belong to you."
                        )
                    }
                )

            if previous_application.status != VerificationApplication.Status.APPROVED:
                raise serializers.ValidationError(
                    {
                        "previous_application": (
                            "Previous application must be approved."
                        )
                    }
                )

            if not hasattr(previous_application, "certificate"):
                raise serializers.ValidationError(
                    {
                        "previous_application": (
                            "Previous application must have a certificate."
                        )
                    }
                )

        else:
            if previous_application is not None:
                raise serializers.ValidationError(
                    {
                        "previous_application": (
                            "Previous application can only be provided "
                            "for re-verification or renewal."
                        )
                    }
                )

        return attrs



class VerificationScheduleSerializer(serializers.ModelSerializer):
    application_number = serializers.CharField(
        source="application.application_number",
        read_only=True,
    )
    scheduled_by_username = serializers.CharField(
        source="scheduled_by.username",
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
            "application_number",
            "scheduled_by",
            "scheduled_by_username",
            "created_at",
            "updated_at",
        ]

    def validate_application(self, application):
        if application.status not in [
            VerificationApplication.Status.ASSIGNED,
            VerificationApplication.Status.SCHEDULED,
        ]:
            raise serializers.ValidationError(
                "Only assigned applications can be scheduled."
            )

        if application.assigned_to is None:
            raise serializers.ValidationError(
                "This application must be assigned to a GATC before scheduling."
            )

        return application


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
            VerificationApplication.Status.SCHEDULED,
            VerificationApplication.Status.INSPECTION,
        ]:
            raise serializers.ValidationError(
                "This application is not available for inspection."
            )

        return application


class PublicInstrumentVerificationSerializer(serializers.ModelSerializer):
    current_certificate = serializers.SerializerMethodField()
    verification_history = serializers.SerializerMethodField()

    class Meta:
        model = Instrument
        fields = [
            "instrument_uid",
            "name",
            "instrument_type",
            "manufacturer",
            "model_number",
            "serial_number",
            "capacity",
            "accuracy",
            "location",
            "status",
            "current_certificate",
            "verification_history",
        ]

    def get_current_certificate(self, instrument):
        certificate = (
            instrument.certificates
            .filter(status="VALID")
            .order_by("-issue_date")
            .first()
        )

        if not certificate:
            return None

        return {
            "certificate_number": certificate.certificate_number,
            "issue_date": certificate.issue_date,
            "valid_until": certificate.valid_until,
            "status": certificate.status,
        }

    def get_verification_history(self, instrument):
        history = []

        for certificate in instrument.certificates.select_related(
            "application"
        ).order_by("-issue_date"):
            history.append(
                {
                    "certificate_number": certificate.certificate_number,
                    "application_number": certificate.application.application_number,
                    "issue_date": certificate.issue_date,
                    "valid_until": certificate.valid_until,
                    "status": certificate.status,
                }
            )

        return history


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

    class Meta:
        model = VerificationDocument
        fields = [
            "id",
            "application",
            "application_number",
            "instrument",
            "instrument_name",
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
            "uploaded_at",
        ]