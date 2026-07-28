from rest_framework.permissions import BasePermission


class IsDoctorOrAdmin(BasePermission):
    """Allow access to doctors and admins only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('doctor', 'admin')


class IsPatient(BasePermission):
    """Allow access to patients only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'patient'


class IsDoctorAdminOrNurse(BasePermission):
    """Allow access to doctors, admins, and nurses."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('doctor', 'admin', 'nurse')


class IsKnowledgeAdmin(BasePermission):
    """Allow access to admins for knowledge base management."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'admin'
