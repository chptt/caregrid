"""
Role-based permission classes for healthcare system.

Implements access control for patient endpoints based on user roles:
- Admin: Full access to all patient data
- Doctor: Access to patient data for treatment purposes
- Nurse: Limited access to patient data for care coordination
- Other roles: No access to patient endpoints

Requirements: 8.5
"""

from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

User = get_user_model()


class IsHealthcareStaff(BasePermission):
    """
    Base permission class for healthcare staff.
    Allows access only to authenticated users with healthcare roles.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and has healthcare role"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow access for healthcare staff roles
        healthcare_roles = ['admin', 'doctor', 'nurse']
        return request.user.role in healthcare_roles


class IsAdminUser(BasePermission):
    """
    Permission class for admin users.
    Allows full access to all patient data and operations.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated admin"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role == 'admin'


class IsDoctorOrAdmin(BasePermission):
    """
    Permission class for doctors and admins.
    Allows access to patient data for medical purposes.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated doctor or admin"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['doctor', 'admin']


class IsNurseDoctorOrAdmin(BasePermission):
    """
    Permission class for nurses, doctors, and admins.
    Allows access to patient data for care coordination and treatment.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated nurse, doctor, or admin"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['nurse', 'doctor', 'admin']


class PatientAccessPermission(BasePermission):
    """
    Granular permission class for patient data access.
    
    Permissions by role and operation:
    - Admin: Full CRUD access to all patient data
    - Doctor: Read/Write access to patient data for treatment
    - Nurse: Read access to patient data for care coordination
    - Others: No access
    """
    
    def has_permission(self, request, view):
        """Check basic authentication and role"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only healthcare staff can access patient endpoints
        healthcare_roles = ['admin', 'doctor', 'nurse']
        return request.user.role in healthcare_roles
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions for specific patient records"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        
        # Admin has full access
        if user_role == 'admin':
            return True
        
        # Doctor has read/write access
        if user_role == 'doctor':
            # Doctors can access patients from their branch or any branch for treatment
            return True
        
        # Nurse has read-only access
        if user_role == 'nurse':
            # Nurses can only read patient data, not modify
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                # Nurses can access patients from their branch
                if hasattr(request.user, 'branch') and hasattr(obj, 'branch'):
                    return request.user.branch == obj.branch
                return True  # Allow if branch info not available
            return False
        
        # Other roles have no access
        return False


class PatientRegistrationPermission(BasePermission):
    """
    Permission class for patient registration.
    
    Allows patient registration by:
    - Admin: Can register patients at any branch
    - Doctor: Can register patients at their branch
    - Nurse: Can register patients at their branch
    """
    
    def has_permission(self, request, view):
        """Check if user can register patients"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only healthcare staff can register patients
        healthcare_roles = ['admin', 'doctor', 'nurse']
        return request.user.role in healthcare_roles


class PatientSearchPermission(BasePermission):
    """
    Permission class for patient search functionality.
    
    Allows patient search by:
    - Admin: Can search all patients across all branches
    - Doctor: Can search patients for treatment purposes
    - Nurse: Can search patients for care coordination
    """
    
    def has_permission(self, request, view):
        """Check if user can search patients"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only healthcare staff can search patients
        healthcare_roles = ['admin', 'doctor', 'nurse']
        return request.user.role in healthcare_roles


def get_permission_classes_for_view(view_name):
    """
    Helper function to get appropriate permission classes for different views.
    
    Args:
        view_name: Name of the view ('register', 'retrieve', 'search', etc.)
    
    Returns:
        List of permission classes
    """
    permission_mapping = {
        'register_patient': [PatientRegistrationPermission],
        'get_patient': [PatientAccessPermission],
        'search_patients': [PatientSearchPermission],
        'get_branches': [IsHealthcareStaff],  # Basic healthcare staff access
    }
    
    return permission_mapping.get(view_name, [IsHealthcareStaff])


def check_branch_access(user, patient):
    """
    Helper function to check if user has access to patient based on branch.
    
    Args:
        user: The requesting user
        patient: The patient object
    
    Returns:
        bool: True if user has access, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    # Admin has access to all branches
    if user.role == 'admin':
        return True
    
    # Other roles need branch matching (if branch info is available)
    if hasattr(user, 'branch') and hasattr(patient, 'branch'):
        return user.branch == patient.branch
    
    # Allow access if branch info is not available (for backward compatibility)
    return True


def get_accessible_branches(user):
    """
    Get list of branches that user can access.
    
    Args:
        user: The requesting user
    
    Returns:
        QuerySet or list of accessible branches
    """
    from core.models import Branch
    
    if not user or not user.is_authenticated:
        return Branch.objects.none()
    
    # Admin can access all branches
    if user.role == 'admin':
        return Branch.objects.all()
    
    # Other roles can only access their assigned branch
    if hasattr(user, 'branch') and user.branch:
        return Branch.objects.filter(id=user.branch.id)
    
    # If no branch assigned, return empty queryset
    return Branch.objects.none()