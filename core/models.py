from django.db import models
from django.utils import timezone
from datetime import date


def _web3_keccak(text: str) -> str:
    """Lazy web3 import so the models module loads on Vercel (no web3 installed)."""
    try:
        from web3 import Web3
        return "0x" + Web3.keccak(text=text).hex()
    except ImportError:
        # Fallback: SHA-256 hex when web3 is not available
        import hashlib
        return "0x" + hashlib.sha256(text.encode()).hexdigest()


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
        dob = self.date_of_birth
        if isinstance(dob, str):
            from datetime import datetime
            dob = datetime.strptime(dob, '%Y-%m-%d').date()
        data = f"{self.name}{dob}{self.contact_email}"
        return _web3_keccak(data)
    
    @staticmethod
    def generate_blockchain_id_static(name, date_of_birth, email):
        """Static method to generate blockchain ID for testing"""
        data = f"{name}{date_of_birth}{email}"
        return _web3_keccak(data)
    
    def calculate_age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        dob = self.date_of_birth
        if isinstance(dob, str):
            from datetime import datetime
            dob = datetime.strptime(dob, '%Y-%m-%d').date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
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