"""
Unit tests for patient retrieval endpoint (Task 11.3)
"""
import pytest
from django.test import Client
from django.urls import reverse
from core.models import Patient, Branch, Doctor, Appointment
from datetime import date, time


@pytest.mark.django_db
class TestPatientRetrievalEndpoint:
    """Test patient retrieval endpoint functionality"""
    
    def setup_method(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test branch
        self.branch = Branch.objects.create(
            name="Test Hospital",
            location="Test City"
        )
        
        # Create test doctor
        self.doctor = Doctor.objects.create(
            name="Dr. Test",
            specialization="General Medicine",
            branch=self.branch
        )
        
        # Create test patient
        self.patient = Patient.objects.create(
            name="John Doe",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            contact_phone="123-456-7890",
            contact_email="john@example.com",
            address="123 Test St",
            branch=self.branch
        )
        
        # Create test appointments
        self.appointment1 = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2026, 1, 20),
            time=time(10, 0),
            branch=self.branch
        )
        
        self.appointment2 = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date(2026, 1, 18),
            time=time(14, 30),
            branch=self.branch
        )
    
    def test_get_patient_by_database_id(self):
        """Test retrieving patient by database ID"""
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify patient data
        assert data['id'] == self.patient.id
        assert data['name'] == "John Doe"
        assert data['blockchain_id'] == self.patient.blockchain_id
        
        # Verify appointments are included
        assert 'appointments' in data
        assert len(data['appointments']) == 2
        
        # Verify appointment structure
        appointment = data['appointments'][0]
        required_fields = ['id', 'doctor', 'doctor_specialization', 'date', 'time', 'branch']
        for field in required_fields:
            assert field in appointment
    
    def test_get_patient_by_blockchain_id(self):
        """Test retrieving patient by blockchain ID"""
        blockchain_id = self.patient.blockchain_id
        response = self.client.get(f'/api/patients/{blockchain_id}/')
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return the same patient
        assert data['id'] == self.patient.id
        assert data['blockchain_id'] == blockchain_id
        assert data['name'] == "John Doe"
    
    def test_get_nonexistent_patient_by_id(self):
        """Test error handling for non-existent patient ID"""
        response = self.client.get('/api/patients/999/')
        
        assert response.status_code == 404
        data = response.json()
        
        assert 'error' in data
        assert 'details' in data
        assert data['error'] == 'Patient not found'
    
    def test_get_nonexistent_patient_by_blockchain_id(self):
        """Test error handling for non-existent blockchain ID"""
        fake_blockchain_id = "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef123456"
        response = self.client.get(f'/api/patients/{fake_blockchain_id}/')
        
        assert response.status_code == 404
        data = response.json()
        
        assert 'error' in data
        assert 'details' in data
        assert data['error'] == 'Patient not found'
        assert 'blockchain ID' in data['details']
    
    def test_appointment_history_ordering(self):
        """Test that appointment history is ordered by date and time (newest first)"""
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        
        assert response.status_code == 200
        data = response.json()
        
        appointments = data['appointments']
        assert len(appointments) == 2
        
        # Should be ordered by date desc, time desc
        assert appointments[0]['date'] == '2026-01-20'  # Newer date first
        assert appointments[1]['date'] == '2026-01-18'
    
    def test_patient_without_appointments(self):
        """Test patient retrieval when patient has no appointments"""
        # Create patient without appointments
        patient_no_appointments = Patient.objects.create(
            name="Jane Doe",
            date_of_birth=date(1985, 5, 15),
            gender="F",
            contact_phone="987-654-3210",
            contact_email="jane@example.com",
            address="456 Test Ave",
            branch=self.branch
        )
        
        response = self.client.get(f'/api/patients/{patient_no_appointments.id}/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['name'] == "Jane Doe"
        assert 'appointments' in data
        assert len(data['appointments']) == 0
    
    def test_response_includes_all_required_fields(self):
        """Test that response includes all required patient fields"""
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            'id', 'name', 'date_of_birth', 'gender', 'contact_phone',
            'contact_email', 'address', 'blockchain_id', 'blockchain_registered',
            'branch', 'branch_name', 'created_at', 'updated_at', 'appointments'
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    def test_appointment_includes_all_required_fields(self):
        """Test that each appointment includes all required fields"""
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        
        assert response.status_code == 200
        data = response.json()
        
        if data['appointments']:
            appointment = data['appointments'][0]
            required_appointment_fields = [
                'id', 'doctor', 'doctor_specialization', 'date', 'time', 'branch'
            ]
            
            for field in required_appointment_fields:
                assert field in appointment, f"Missing required appointment field: {field}"