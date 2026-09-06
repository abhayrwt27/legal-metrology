from django.urls import path

from .views import (
    InstrumentDetailView,
    InstrumentListCreateView,
)


urlpatterns = [
    path("", InstrumentListCreateView.as_view(), name="instrument-list-create"),
    path("<int:pk>/", InstrumentDetailView.as_view(), name="instrument-detail"),
]