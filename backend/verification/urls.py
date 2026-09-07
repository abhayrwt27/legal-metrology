from django.urls import path

from .views import (
    VerificationApplicationDetailView,
    VerificationApplicationListCreateView,
)


urlpatterns = [
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
]
