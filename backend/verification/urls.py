from django.urls import path

from .views import (
    ApplicationDecisionView,
    AssignApplicationView,
    CertificateDetailView,
    CertificateExpiryAlertView,
    CertificateQRCodeView,
    DashboardView,
    GATCInspectionCreateView,
    GATCInspectionDetailView,
    OfficerApplicationDetailView,
    OfficerApplicationListView,
    PublicCertificateVerificationView,
    PublicInstrumentVerificationView,
    VerificationApplicationDetailView,
    VerificationApplicationListCreateView,
    VerificationScheduleCreateView,
    InstrumentQRCodeView,
    VerificationDocumentListCreateView,
    SearchView,
)


urlpatterns = [
    # Owner
    path(
        "",
        VerificationApplicationListCreateView.as_view(),
        name="verification-list-create",
    ),

    #certificate
    path(
        "certificates/<int:pk>/",
        CertificateDetailView.as_view(),
        name="certificate-detail",
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

    path(
        "officer/schedules/",
        VerificationScheduleCreateView.as_view(),
        name="verification-schedule-create",
    ),

    # LMO / Admin decision
    path(
        "officer/applications/<int:pk>/decision/",
        ApplicationDecisionView.as_view(),
        name="application-decision",
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

    path(
        "public/instruments/<uuid:instrument_uid>/",
        PublicInstrumentVerificationView.as_view(),
        name="public-instrument-verification",
    ),

    path(
        "public/instruments/<uuid:instrument_uid>/qr/",
        InstrumentQRCodeView.as_view(),
        name="instrument-qr",
    ),

    path(
        "public/certificates/<str:certificate_number>/",
        PublicCertificateVerificationView.as_view(),
        name="public-certificate-verification",
    ),

    path(
        "public/certificates/<str:certificate_number>/qr/",
        CertificateQRCodeView.as_view(),
        name="certificate-qr",
    ),

    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),

    path(
        "certificates/expiry-alerts/",
        CertificateExpiryAlertView.as_view(),
        name="certificate-expiry-alerts",
    ),

    path(
        "documents/",
        VerificationDocumentListCreateView.as_view(),
        name="verification-documents",
    ),

    path(
        "search/",
        SearchView.as_view(),
        name="search",
    ),
]