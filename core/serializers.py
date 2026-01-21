from rest_framework import serializers
from .models import Patient, Branch, Appointment, Doctor
from datetime import date, datetime


class PatientRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for patient registration with validation"""
    
    class Meta:
        model = Patient
        fields = [
            'name', 'date_of_birth', 'gender', 'contact_phone', 
            'contact_email', 'address', 'branch', 'blockchain_id'
        ]
        read_only_fields = ['blockchain_id']
    
    def validate_name(self, value):
        """Validate patient name"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long")
        if len(value) > 100:
            raise serializers.ValidationError("Name cannot exceed 100 characters")
        return value.strip()
    
    def validate_date_of_birth(self, value):
        """Validate date of birth"""
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future")
        if value.year < 1900:
            raise serializers.ValidationError("Date of birth cannot be before 1900")
        return value
    
    def validate_contact_email(self, value):
        """Validate email format"""
        if not value:
            raise serializers.ValidationError("Email is required")
        return value.lower().strip()
    
    def validate_contact_phone(self, value):
        """Validate phone number"""
        if not value:
            raise serializers.ValidationError("Phone number is required")
        # Basic phone validation - remove spaces and check length
        cleaned_phone = ''.join(value.split())
        if len(cleaned_phone) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value.strip()
    
    def validate_gender(self, value):
        """Validate gender"""
        allowed_genders = ['M', 'F', 'Male', 'Female', 'Other']
        if value not in allowed_genders:
            raise serializers.ValidationError(f"Gender must be one of: {', '.join(allowed_genders)}")
        return value
    
    def validate_branch(self, value):
        """Validate branch exists"""
        if not Branch.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Invalid branch specified")
        return value


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for patient retrieval"""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'name', 'date_of_birth', 'gender', 'contact_phone',
            'contact_email', 'address', 'blockchain_id', 'blockchain_registered',
            'branch', 'branch_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'blockchain_id', 'blockchain_registered', 
            'created_at', 'updated_at'
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for appointment creation and retrieval"""
    
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_blockchain_id = serializers.CharField(source='patient.blockchain_id', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'patient_blockchain_id',
            'doctor', 'doctor_name', 'doctor_specialization',
            'date', 'time', 'branch', 'branch_name'
        ]
    
    def validate_date(self, value):
        """Validate appointment date"""
        if value < date.today():
            raise serializers.ValidationError("Appointment date cannot be in the past")
        return value
    
    def validate_patient(self, value):
        """Validate patient exists and has blockchain ID"""
        if not Patient.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Invalid patient specified")
        
        patient = Patient.objects.get(id=value.id)
        if not patient.blockchain_id:
            raise serializers.ValidationError("Patient must have a blockchain ID to book appointments")
        
        return value
    
    def validate_doctor(self, value):
        """Validate doctor exists"""
        if not Doctor.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Invalid doctor specified")
        return value
    
    def validate_branch(self, value):
        """Validate branch exists"""
        if not Branch.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Invalid branch specified")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Check if doctor works at the specified branch
        if data['doctor'].branch != data['branch']:
            raise serializers.ValidationError({
                'doctor': f"Doctor {data['doctor'].name} does not work at branch {data['branch'].name}"
            })
        
        # Check for duplicate appointments (same patient, doctor, date, time)
        if Appointment.objects.filter(
            patient=data['patient'],
            doctor=data['doctor'],
            date=data['date'],
            time=data['time']
        ).exists():
            raise serializers.ValidationError(
                "An appointment already exists for this patient with this doctor at the same date and time"
            )
        
        return data


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for doctor information"""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialization', 'branch', 'branch_name']