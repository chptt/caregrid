from django.db import models
from django.utils import timezone
from web3 import Web3
from datetime import date


class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Patient(models.Model):
    # Core patient information
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField(default='1990-01-01')
    gender = models.CharField(max_length=10)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    address = models.TextField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    
    # Legacy field for backward compatibility
    age = models.IntegerField(null=True, blank=True)
    
    # Blockchain integration fields
    blockchain_id = models.CharField(max_length=66, unique=True, blank=True, null=True)  # bytes32 hex
    blockchain_registered = models.BooleanField(default=False)
    registration_tx_hash = models.CharField(max_length=66, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_blockchain_id(self):
        """Generate unique blockchain ID from patient data"""
        if not self.date_of_birth or not self.contact_email:
            return None
        data = f"{self.name}{self.date_of_birth}{self.contact_email}"
        return "0x" + Web3.keccak(text=data).hex()
    
    @staticmethod
    def generate_blockchain_id_static(name, date_of_birth, email):
        """Static method to generate blockchain ID for testing"""
        data = f"{name}{date_of_birth}{email}"
        return "0x" + Web3.keccak(text=data).hex()
    
    def calculate_age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate age and blockchain ID"""
        # Auto-calculate age from date_of_birth
        if self.date_of_birth:
            self.age = self.calculate_age()
        
        # Auto-generate blockchain ID if not set
        if not self.blockchain_id and self.date_of_birth and self.contact_email:
            self.blockchain_id = self.generate_blockchain_id()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.patient.name} with {self.doctor.name} on {self.date}"