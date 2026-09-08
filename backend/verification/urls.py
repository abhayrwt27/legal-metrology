from django.urls import path

from .views import (
    AssignApplicationView,
    GATCInspectionCreateView,
    GATCInspectionDetailView,
    OfficerApplicationDetailView,
    OfficerApplicationListView,
    VerificationApplicationDetailView,
    VerificationApplicationListCreateView,
)


urlpatterns = [
    # Owner
    path(
        "",
        VerificationApplicationListCreateView.as_view(),
        name="verification-list-create",
    ),

    path(
        "<int:pk>/",
        VerificationApplicationDetailView.as_view(),
        name="verification-detail",
    ),

    # Officer
    path(
        "officer/applications/",
        OfficerApplicationListView.as_view(),
        name="officer-application-list",
    ),

    path(
        "officer/applications/<int:pk>/",
        OfficerApplicationDetailView.as_view(),
        name="officer-application-detail",
    ),

    # LMO / Admin assignment
    path(
        "officer/applications/<int:pk>/assign/",
        AssignApplicationView.as_view(),
        name="assign-application",
    ),

    # GATC inspection
    path(
        "officer/inspections/",
        GATCInspectionCreateView.as_view(),
        name="gatc-inspection-create",
    ),

    path(
        "officer/inspections/<int:pk>/",
        GATCInspectionDetailView.as_view(),
        name="gatc-inspection-detail",
    ),
]