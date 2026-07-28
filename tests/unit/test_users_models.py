"""
Unit tests for users models: CustomUser
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from core.models import Branch

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Test cases for CustomUser model"""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test Hospital",
            location="Test Location"
        )
    
    def test_custom_user_creation(self):
        """Test basic custom user creation"""
        user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            role="doctor",
            branch=self.branch
        )
        
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, "doctor")
        self.assertEqual(user.branch, self.branch)
        self.assertTrue(user.check_password("testpass123"))
    
    def test_custom_user_role_choices(self):
        """Test all available role choices"""
        valid_roles = [
            'admin', 'doctor', 'patient', 'receptionist', 'lab',
            'nurse', 'pharmacy', 'ot', 'scan', 'room_mgr',
            'billing', 'records', 'dietician', 'sanitation'
        ]
        
        for i, role in enumerate(valid_roles):
            user = User.objects.create_user(
                username=f"user_{i}",
                password="testpass123",
                role=role,
                branch=self.branch
            )
            self.assertEqual(user.role, role)
    
    def test_custom_user_without_branch(self):
        """Test user creation without branch (should be allowed)"""
        user = User.objects.create_user(
            username="nobranch",
            password="testpass123",
            role="admin"
            # branch is optional (null=True, blank=True)
        )
        
        self.assertEqual(user.username, "nobranch")
        self.assertEqual(user.role, "admin")
        self.assertIsNone(user.branch)
    
    def test_custom_user_branch_relationship(self):
        """Test user-branch foreign key relationship"""
        user = User.objects.create_user(
            username="branchuser",
            password="testpass123",
            role="nurse",
            branch=self.branch
        )
        
        self.assertEqual(user.branch.name, "Test Hospital")
        self.assertEqual(user.branch.location, "Test Location")
    
    def test_custom_user_superuser_creation(self):
        """Test superuser creation"""
        superuser = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
            email="admin@example.com",
            role="admin",
            branch=self.branch
        )
        
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertEqual(superuser.role, "admin")
    
    def test_custom_user_username_uniqueness(self):
        """Test username uniqueness constraint"""
        User.objects.create_user(
            username="unique_user",
            password="pass123",
            role="doctor"
        )
        
        # Creating another user with same username should fail
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="unique_user",
                password="pass456",
                role="nurse"
            )
    
    def test_custom_user_role_validation(self):
        """Test role field validation"""
        user = User(
            username="testuser",
            role="doctor",
            branch=self.branch
        )
        user.set_password("testpass123")
        
        # Valid role should pass validation
        user.full_clean()  # Should not raise ValidationError
        
        # Test with invalid role
        user.role = "invalid_role"
        with self.assertRaises(ValidationError):
            user.full_clean()
    
    def test_custom_user_role_max_length(self):
        """Test role field max length constraint"""
        user = User(
            username="testuser",
            role="a" * 21,  # Exceeds max_length=20
            branch=self.branch
        )
        user.set_password("testpass123")
        
        with self.assertRaises(ValidationError):
            user.full_clean()
    
    def test_custom_user_inherited_fields(self):
        """Test inherited AbstractUser fields work correctly"""
        user = User.objects.create_user(
            username="inherited_test",
            password="testpass123",
            email="inherited@example.com",
            first_name="John",
            last_name="Doe",
            role="patient",
            branch=self.branch
        )
        
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.email, "inherited@example.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_custom_user_authentication(self):
        """Test user authentication functionality"""
        user = User.objects.create_user(
            username="auth_test",
            password="secure_password_123",
            role="doctor",
            branch=self.branch
        )
        
        # Test correct password
        self.assertTrue(user.check_password("secure_password_123"))
        
        # Test incorrect password
        self.assertFalse(user.check_password("wrong_password"))
    
    def test_custom_user_multiple_branches(self):
        """Test users can be assigned to different branches"""
        branch1 = Branch.objects.create(name="Branch 1", location="Location 1")
        branch2 = Branch.objects.create(name="Branch 2", location="Location 2")
        
        user1 = User.objects.create_user(
            username="user1",
            password="pass123",
            role="doctor",
            branch=branch1
        )
        
        user2 = User.objects.create_user(
            username="user2",
            password="pass123",
            role="nurse",
            branch=branch2
        )
        
        self.assertEqual(user1.branch, branch1)
        self.assertEqual(user2.branch, branch2)
        self.assertNotEqual(user1.branch, user2.branch)
    
    def test_custom_user_role_display_names(self):
        """Test role choice display names"""
        user = User(role="room_mgr")
        
        # Get the display name for the role
        role_display = user.get_role_display()
        self.assertEqual(role_display, "Room Allocation Manager")
        
        # Test another role
        user.role = "ot"
        role_display = user.get_role_display()
        self.assertEqual(role_display, "Operation Theatre")
    
    def test_custom_user_str_representation(self):
        """Test string representation uses inherited AbstractUser __str__"""
        user = User.objects.create_user(
            username="str_test",
            password="pass123",
            role="admin"
        )
        
        # AbstractUser uses username as string representation
        self.assertEqual(str(user), "str_test")