from rest_framework import serializers

from .models import Instrument


class InstrumentSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Instrument
        fields = [
            "id",
            "instrument_uid",
            "owner",
            "name",
            "instrument_type",
            "manufacturer",
            "model_number",
            "serial_number",
            "capacity",
            "accuracy",
            "location",
            "purchase_date",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "instrument_uid",
            "owner",
            "status",
            "created_at",
            "updated_at",
        ]