from rest_framework import permissions, viewsets

from .models import Instrument
from .serializers import InstrumentSerializer


class InstrumentViewSet(viewsets.ModelViewSet):
    serializer_class = InstrumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Instrument.objects
            .filter(owner=self.request.user)
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
