from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Instrument
from .serializers import InstrumentSerializer


class InstrumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InstrumentSerializer

    def get_queryset(self):
        return Instrument.objects.filter(owner=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class InstrumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InstrumentSerializer

    def get_queryset(self):
        return Instrument.objects.filter(owner=self.request.user)