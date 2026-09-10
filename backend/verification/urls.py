from django.urls import path

from .views import (
    ApplicationDecisionView,
    AssignApplicationView,
    CertificateDetailView,
    CertificateExpiryAlertView,
    CertificateListView,
    DashboardView,
    InspectionCreateView,
    OfficerApplicationListView,
    PublicCertificateQRView,
    PublicCertificateVerificationView,
    PublicInstrumentLookupView,
    PublicInstrumentQRView,
    PublicInstrumentVerificationView,
    SearchView,
    VerificationApplicationDetailView,
    VerificationApplicationListCreateView,
    VerificationDocumentListCreateView,
    VerificationScheduleCreateView,
)


urlpatterns = [
    # -------------------------------------------------------------------------
    # Owner applications
    # -------------------------------------------------------------------------
    path(
        "",
        VerificationApplicationListCreateView.as_view(),
        name="verification-application-list-create",
    ),
    path(
        "<int:pk>/",
        VerificationApplicationDetailView.as_view(),
        name="verification-application-detail",
    ),

    # -------------------------------------------------------------------------
    # Officer applications
    # -------------------------------------------------------------------------
    path(
        "officer/applications/",
        OfficerApplicationListView.as_view(),
        name="officer-application-list",
    ),
    path(
        "officer/applications/<int:pk>/assign/",
        AssignApplicationView.as_view(),
        name="assign-application",
    ),
    path(
        "officer/applications/<int:pk>/decision/",
        ApplicationDecisionView.as_view(),
        name="application-decision",
    ),

    # -------------------------------------------------------------------------
    # Scheduling
    # -------------------------------------------------------------------------
    path(
        "officer/schedules/",
        VerificationScheduleCreateView.as_view(),
        name="verification-schedule-create",
    ),

    # -------------------------------------------------------------------------
    # Inspections
    # -------------------------------------------------------------------------
    path(
        "officer/inspections/",
        InspectionCreateView.as_view(),
        name="inspection-create",
    ),

    # -------------------------------------------------------------------------
    # Certificates
    # -------------------------------------------------------------------------
    path(
        "certificates/",
        CertificateListView.as_view(),
        name="certificate-list",
    ),
    path(
        "certificates/expiry-alerts/",
        CertificateExpiryAlertView.as_view(),
        name="certificate-expiry-alerts",
    ),
    path(
        "certificates/<int:pk>/",
        CertificateDetailView.as_view(),
        name="certificate-detail",
    ),

    # -------------------------------------------------------------------------
    # Dashboard
    # -------------------------------------------------------------------------
    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------
    path(
        "search/",
        SearchView.as_view(),
        name="search",
    ),

    # -------------------------------------------------------------------------
    # Documents
    # -------------------------------------------------------------------------
    path(
        "documents/",
        VerificationDocumentListCreateView.as_view(),
        name="verification-document-list-create",
    ),

    # -------------------------------------------------------------------------
    # Public instrument verification
    # -------------------------------------------------------------------------
    path(
        "public/instruments/<uuid:instrument_uid>/",
        PublicInstrumentVerificationView.as_view(),
        name="public-instrument-verification",
    ),
    path(
        "public/instruments/<uuid:instrument_uid>/qr/",
        PublicInstrumentQRView.as_view(),
        name="public-instrument-qr",
    ),
    path(
        "public/instruments/lookup/",
        PublicInstrumentLookupView.as_view(),
        name="public-instrument-lookup",
    ),

    # -------------------------------------------------------------------------
    # Public certificate verification
    # -------------------------------------------------------------------------
    path(
        "public/certificates/<str:certificate_number>/",
        PublicCertificateVerificationView.as_view(),
        name="public-certificate-verification",
    ),
    path(
        "public/certificates/<str:certificate_number>/qr/",
        PublicCertificateQRView.as_view(),
        name="public-certificate-qr",
    ),
]