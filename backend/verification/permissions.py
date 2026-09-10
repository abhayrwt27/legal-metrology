from rest_framework.permissions import BasePermission


class IsLMO(BasePermission):
    message = "Only a Legal Metrology Officer can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "LMO"
        )


class IsGATC(BasePermission):
    message = "Only a Government Approved Test Centre can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "GATC"
        )


class IsLMOOrAdmin(BasePermission):
    message = "Only an LMO or Admin can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["LMO", "ADMIN"]
        )


class IsOfficer(BasePermission):
    message = "Only an LMO, GATC or Admin can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["LMO", "GATC", "ADMIN"]
        )


class IsOwner(BasePermission):
    message = "Only an instrument owner can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "OWNER"
        )
