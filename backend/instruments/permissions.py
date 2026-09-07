from rest_framework.permissions import BasePermission


class IsLMO(BasePermission):
    """
    Allows access only to Legal Metrology Officers.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "LMO"
        )


class IsGATC(BasePermission):
    """
    Allows access only to Government Approved Test Centres.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "GATC"
        )


class IsLMOOrAdmin(BasePermission):
    """
    Allows access to LMOs and Admins.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["LMO", "ADMIN"]
        )


class IsOfficer(BasePermission):
    """
    Allows access to LMO, GATC, or Admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["LMO", "GATC", "ADMIN"]
        )