from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import Branch

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('receptionist', 'Receptionist'),
        ('lab', 'Lab Technician'),
        ('nurse', 'Nursing Station'),
        ('pharmacy', 'Pharmacy'),
        ('ot', 'Operation Theatre'),
        ('scan', 'Scanning Room'),
        ('room_mgr', 'Room Allocation Manager'),
        ('billing', 'Billing'),
        ('records', 'Medical Records Officer'),
        ('dietician', 'Dietician'),
        ('sanitation', 'Sanitation Manager'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)