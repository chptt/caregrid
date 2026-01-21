"""
Unit tests for patient endpoint role-based access control.

Tests permission classes and access control for patient endpoints
based on user roles (admin, doctor, nurse).

Requirements: 8.5
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import Mock, patch
from datetime import date

from core.models import Patient, Branch, Doctor
from core.permissions import (
    IsHealthcareStaff,
    IsAdminUser,
    IsDoctorOrAdmin,
    IsNurseDoctorOrAdmin,
    PatientAccessPermission,
    PatientRegistrationPermission,
    PatientSearchPermission,
    check_branch_access,
    get_accessible_branches
)

User = get_user_model()


class PermissionClassesTestCase(TestCase):
    """Test individual permission classes"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create test branch
        self.branch = Branch.objects.create(
            name="Test Hospital",
            location="Test City"
        )
        
        # Create test users with different roles
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123",
            role="admin",
            branch=self.branch
        )
        
        self.doctor_user = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role="doctor",
            branch=self.branch
        )
        
        self.nurse_user = User.objects.create_user(
            username="nurse",
            password="testpass123",
            role="nurse",
            branch=self.branch
        )
        
        self.patient_user = User.objects.create_user(
            username="patient",
            password="testpass123",
            role="patient",
            branch=self.branch
        )
        
        self.unauthenticated_request = self.factory.get('/test/')
        self.unauthenticated_request.user = None
    
    def test_is_healthcare_staff_permission(self):
        """Test IsHealthcareStaff permission class"""
        permission = IsHealthcareStaff()
        
        # Test admin user
        request = self.factory.get('/test/')
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test doctor user
        request.user = self.doctor_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test nurse user
        request.user = self.nurse_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test patient user (should be denied)
        request.user = self.patient_user
        self.assertFalse(permission.has_permission(request, None))
        
        # Test unauthenticated user
        self.assertFalse(permission.has_permission(self.unauthenticated_request, None))
    
    def test_is_admin_user_permission(self):
        """Test IsAdminUser permission class"""
        permission = IsAdminUser()
        
        # Test admin user
        request = self.factory.get('/test/')
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test doctor user (should be denied)
        request.user = self.doctor_user
        self.assertFalse(permission.has_permission(request, None))
        
        # Test nurse user (should be denied)
        request.user = self.nurse_user
        self.assertFalse(permission.has_permission(request, None))
        
        # Test unauthenticated user
        self.assertFalse(permission.has_permission(self.unauthenticated_request, None))
    
    def test_is_doctor_or_admin_permission(self):
        """Test IsDoctorOrAdmin permission class"""
        permission = IsDoctorOrAdmin()
        
        # Test admin user
        request = self.factory.get('/test/')
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test doctor user
        request.user = self.doctor_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test nurse user (should be denied)
        request.user = self.nurse_user
        self.assertFalse(permission.has_permission(request, None))
        
        # Test unauthenticated user
        self.assertFalse(permission.has_permission(self.unauthenticated_request, None))
    
    def test_is_nurse_doctor_or_admin_permission(self):
        """Test IsNurseDoctorOrAdmin permission class"""
        permission = IsNurseDoctorOrAdmin()
        
        # Test admin user
        request = self.factory.get('/test/')
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test doctor user
        request.user = self.doctor_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test nurse user
        request.user = self.nurse_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Test patient user (should be denied)
        request.user = self.patient_user
        self.assertFalse(permission.has_permission(request, None))
        
        # Test unauthenticated user
        self.assertFalse(permission.has_permission(self.unauthenticated_request, None))


class PatientAccessPermissionTestCase(TestCase):
    """Test PatientAccessPermission class"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create test branches
        self.branch1 = Branch.objects.create(
            name="Hospital A",
            location="City A"
        )
        
        self.branch2 = Branch.objects.create(
            name="Hospital B",
            location="City B"
        )
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123",
            role="admin",
            branch=self.branch1
        )
        
        self.doctor_user = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role="doctor",
            branch=self.branch1
        )
        
        self.nurse_user = User.objects.create_user(
            username="nurse",
            password="testpass123",
            role="nurse",
            branch=self.branch1
        )
        
        # Create test patient
        self.patient = Patient.objects.create(
            name="Test Patient",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            contact_phone="1234567890",
            contact_email="test@example.com",
            address="Test Address",
            branch=self.branch1
        )
        
        self.permission = PatientAccessPermission()
    
    def test_has_permission_basic_auth(self):
        """Test basic authentication and role checking"""
        # Test admin user
        request = self.factory.get('/test/')
        request.user = self.admin_user
        self.assertTrue(self.permission.has_permission(request, None))
        
        # Test doctor user
        request.user = self.doctor_user
        self.assertTrue(self.permission.has_permission(request, None))
        
        # Test nurse user
        request.user = self.nurse_user
        self.assertTrue(self.permission.has_permission(request, None))
        
        # Test unauthenticated user
        request.user = None
        self.assertFalse(self.permission.has_permission(request, None))
    
    def test_has_object_permission_admin(self):
        """Test object-level permissions for admin users"""
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        # Admin should have full access
        self.assertTrue(self.permission.has_object_permission(request, None, self.patient))
        
        # Test with POST request (write access)
        request = self.factory.post('/test/')
        request.user = self.admin_user
        self.assertTrue(self.permission.has_object_permission(request, None, self.patient))
    
    def test_has_object_permission_doctor(self):
        """Test object-level permissions for doctor users"""
        # Test GET request (read access)
        request = self.factory.get('/test/')
        request.user = self.doctor_user
        self.assertTrue(self.permission.has_object_permission(request, None, self.patient))
        
        # Test POST request (write access)
        request = self.factory.post('/test/')
        request.user = self.doctor_user
        self.assertTrue(self.permission.has_object_permission(request, None, self.patient))
    
    def test_has_object_permission_nurse(self):
        """Test object-level permissions for nurse users"""
        # Test GET request (read access) - should be allowed
        request = self.factory.get('/test/')
        request.user = self.nurse_user
        self.assertTrue(self.permission.has_object_permission(request, None, self.patient))
        
        # Test POST request (write access) - should be denied
        request = self.factory.post('/test/')
        request.user = self.nurse_user
        self.assertFalse(self.permission.has_object_permission(request, None, self.patient))
        
        # Test PUT request (write access) - should be denied
        request = self.factory.put('/test/')
        request.user = self.nurse_user
        self.assertFalse(self.permission.has_object_permission(request, None, self.patient))
        
        # Test DELETE request (write access) - should be denied
        request = self.factory.delete('/test/')
        request.user = self.nurse_user
        self.assertFalse(self.permission.has_object_permission(request, None, self.patient))
    
    def test_has_object_permission_branch_access(self):
        """Test branch-based access control for nurses"""
        # Create nurse from different branch
        nurse_other_branch = User.objects.create_user(
            username="nurse2",
            password="testpass123",
            role="nurse",
            branch=self.branch2
        )
        
        # Create patient from different branch
        patient_other_branch = Patient.objects.create(
            name="Other Patient",
            date_of_birth=date(1990, 1, 1),
            gender="F",
            contact_phone="1234567890",
            contact_email="other@example.com",
            address="Other Address",
            branch=self.branch2
        )
        
        # Nurse should have access to patient from same branch
        request = self.factory.get('/test/')
        request.user = self.nurse_user
        self.assertTrue(self.permission.has_object_permission(request, None, self.patient))
        
        # Nurse should NOT have access to patient from different branch
        self.assertFalse(self.permission.has_object_permission(request, None, patient_other_branch))
        
        # Nurse from other branch should have access to their branch patient
        request.user = nurse_other_branch
        self.assertTrue(self.permission.has_object_permission(request, None, patient_other_branch))


class HelperFunctionsTestCase(TestCase):
    """Test helper functions for access control"""
    
    def setUp(self):
        # Create test branches
        self.branch1 = Branch.objects.create(
            name="Hospital A",
            location="City A"
        )
        
        self.branch2 = Branch.objects.create(
            name="Hospital B",
            location="City B"
        )
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123",
            role="admin",
            branch=self.branch1
        )
        
        self.doctor_user = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role="doctor",
            branch=self.branch1
        )
        
        self.nurse_user = User.objects.create_user(
            username="nurse",
            password="testpass123",
            role="nurse",
            branch=self.branch2
        )
        
        # Create test patient
        self.patient = Patient.objects.create(
            name="Test Patient",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            contact_phone="1234567890",
            contact_email="test@example.com",
            address="Test Address",
            branch=self.branch1
        )
    
    def test_check_branch_access(self):
        """Test check_branch_access helper function"""
        # Admin should have access to all branches
        self.assertTrue(check_branch_access(self.admin_user, self.patient))
        
        # Doctor from same branch should have access
        self.assertTrue(check_branch_access(self.doctor_user, self.patient))
        
        # Nurse from different branch should NOT have access
        self.assertFalse(check_branch_access(self.nurse_user, self.patient))
        
        # Unauthenticated user should not have access
        self.assertFalse(check_branch_access(None, self.patient))
    
    def test_get_accessible_branches(self):
        """Test get_accessible_branches helper function"""
        # Admin should have access to all branches
        admin_branches = get_accessible_branches(self.admin_user)
        self.assertEqual(admin_branches.count(), 2)
        self.assertIn(self.branch1, admin_branches)
        self.assertIn(self.branch2, admin_branches)
        
        # Doctor should have access to their branch only
        doctor_branches = get_accessible_branches(self.doctor_user)
        self.assertEqual(doctor_branches.count(), 1)
        self.assertIn(self.branch1, doctor_branches)
        self.assertNotIn(self.branch2, doctor_branches)
        
        # Nurse should have access to their branch only
        nurse_branches = get_accessible_branches(self.nurse_user)
        self.assertEqual(nurse_branches.count(), 1)
        self.assertIn(self.branch2, nurse_branches)
        self.assertNotIn(self.branch1, nurse_branches)
        
        # Unauthenticated user should have no access
        unauth_branches = get_accessible_branches(None)
        self.assertEqual(unauth_branches.count(), 0)


class PatientEndpointAccessTestCase(APITestCase):
    """Integration tests for patient endpoint access control"""
    
    def setUp(self):
        # Create test branch
        self.branch = Branch.objects.create(
            name="Test Hospital",
            location="Test City"
        )
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123",
            role="admin",
            branch=self.branch
        )
        
        self.doctor_user = User.objects.create_user(
            username="doctor",
            password="testpass123",
            role="doctor",
            branch=self.branch
        )
        
        self.nurse_user = User.objects.create_user(
            username="nurse",
            password="testpass123",
            role="nurse",
            branch=self.branch
        )
        
        self.patient_user = User.objects.create_user(
            username="patient",
            password="testpass123",
            role="patient",
            branch=self.branch
        )
        
        # Create test patient
        self.patient = Patient.objects.create(
            name="Test Patient",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            contact_phone="1234567890",
            contact_email="test@example.com",
            address="Test Address",
            branch=self.branch
        )
    
    @patch('core.patient_views.BlockchainService')
    def test_patient_registration_access_control(self, mock_blockchain):
        """Test access control for patient registration endpoint"""
        # Mock blockchain service
        mock_blockchain.return_value.register_patient.return_value = ("0x123", True)
        
        registration_data = {
            "name": "New Patient",
            "date_of_birth": "1985-05-15",
            "gender": "F",
            "contact_phone": "9876543210",
            "contact_email": "new@example.com",
            "address": "New Address",
            "branch": self.branch.id
        }
        
        # Test admin access - should be allowed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/patients/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test doctor access - should be allowed
        self.client.force_authenticate(user=self.doctor_user)
        registration_data['contact_email'] = 'doctor@example.com'  # Avoid duplicate
        response = self.client.post('/api/patients/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test nurse access - should be allowed
        self.client.force_authenticate(user=self.nurse_user)
        registration_data['contact_email'] = 'nurse@example.com'  # Avoid duplicate
        response = self.client.post('/api/patients/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test patient access - should be denied
        self.client.force_authenticate(user=self.patient_user)
        registration_data['contact_email'] = 'patient@example.com'  # Avoid duplicate
        response = self.client.post('/api/patients/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test unauthenticated access - should be denied
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/patients/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_patient_retrieval_access_control(self):
        """Test access control for patient retrieval endpoint"""
        # Test admin access - should be allowed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test doctor access - should be allowed
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test nurse access - should be allowed
        self.client.force_authenticate(user=self.nurse_user)
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test patient access - should be denied
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test unauthenticated access - should be denied
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_patient_search_access_control(self):
        """Test access control for patient search endpoint"""
        # Test admin access - should be allowed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/patients/search/?q=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test doctor access - should be allowed
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get('/api/patients/search/?q=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test nurse access - should be allowed
        self.client.force_authenticate(user=self.nurse_user)
        response = self.client.get('/api/patients/search/?q=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test patient access - should be denied
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get('/api/patients/search/?q=Test')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test unauthenticated access - should be denied
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/patients/search/?q=Test')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_branches_access_control(self):
        """Test access control for branches endpoint"""
        # Test admin access - should be allowed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/branches/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test doctor access - should be allowed
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get('/api/branches/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test nurse access - should be allowed
        self.client.force_authenticate(user=self.nurse_user)
        response = self.client.get('/api/branches/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test patient access - should be denied
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get('/api/branches/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test unauthenticated access - should be denied
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/branches/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)