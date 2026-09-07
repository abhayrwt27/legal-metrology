from django.urls import path

from .views import (
    AssignApplicationView,
    OfficerApplicationDetailView,
    OfficerApplicationListView,
    VerificationApplicationDetailView,
    VerificationApplicationListCreateView,
)

urlpatterns = [
    # Owner endpoints
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

    # LMO / GATC / ADMIN endpoints
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
    path(
        "officer/applications/<int:pk>/assign/",
        AssignApplicationView.as_view(),
        name="assign-application",
    ),
]