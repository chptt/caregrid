"""
Unit tests for core models: Branch, Doctor, Patient, Appointment
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, time, timedelta
from core.models import Branch, Doctor, Patient, Appointment


class BranchModelTest(TestCase):
    """Test cases for Branch model"""
    
    def test_branch_creation(self):
        """Test basic branch creation"""
        branch = Branch.objects.create(
            name="Main Hospital",
            location="123 Main St, City"
        )
        self.assertEqual(branch.name, "Main Hospital")
        self.assertEqual(branch.location, "123 Main St, City")
        self.assertEqual(str(branch), "Main Hospital")
    
    def test_branch_str_representation(self):
        """Test string representation of branch"""
        branch = Branch(name="Test Branch")
        self.assertEqual(str(branch), "Test Branch")


class DoctorModelTest(TestCase):
    """Test cases for Doctor model"""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )
    
    def test_doctor_creation(self):
        """Test basic doctor creation"""
        doctor = Doctor.objects.create(
            name="Dr. Smith",
            specialization="Cardiology",
            branch=self.branch
        )
        self.assertEqual(doctor.name, "Dr. Smith")
        self.assertEqual(doctor.specialization, "Cardiology")
        self.assertEqual(doctor.branch, self.branch)
        self.assertEqual(str(doctor), "Dr. Smith")
    
    def test_doctor_branch_relationship(self):
        """Test doctor-branch foreign key relationship"""
        doctor = Doctor.objects.create(
            name="Dr. Johnson",
            specialization="Neurology",
            branch=self.branch
        )
        self.assertEqual(doctor.branch.name, "Test Branch")
    
    def test_doctor_str_representation(self):
        """Test string representation of doctor"""
        doctor = Doctor(name="Dr. Test")
        self.assertEqual(str(doctor), "Dr. Test")


class PatientModelTest(TestCase):
    """Test cases for Patient model"""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )
    
    def test_patient_creation_basic(self):
        """Test basic patient creation with original fields"""
        patient = Patient.objects.create(
            name="John Doe",
            age=30,
            gender="Male",
            branch=self.branch
        )
        self.assertEqual(patient.name, "John Doe")
        self.assertEqual(patient.age, 30)
        self.assertEqual(patient.gender, "Male")
        self.assertEqual(patient.branch, self.branch)
        self.assertFalse(patient.blockchain_registered)
        self.assertEqual(str(patient), "John Doe")
    
    def test_patient_creation_enhanced(self):
        """Test patient creation with enhanced fields"""
        patient = Patient.objects.create(
            name="Jane Smith",
            age=25,
            gender="Female",
            branch=self.branch,
            date_of_birth=date(1998, 5, 15),
            contact_phone="555-1234",
            contact_email="jane@example.com",
            address="456 Oak St"
        )
        self.assertEqual(patient.date_of_birth, date(1998, 5, 15))
        self.assertEqual(patient.contact_phone, "555-1234")
        self.assertEqual(patient.contact_email, "jane@example.com")
        self.assertEqual(patient.address, "456 Oak St")
    
    def test_patient_default_values(self):
        """Test patient model default values"""
        patient = Patient.objects.create(
            name="Test Patient",
            age=40,
            gender="Male",
            branch=self.branch
        )
        self.assertEqual(patient.contact_phone, '')
        self.assertEqual(patient.contact_email, '')
        self.assertEqual(patient.address, '')
        self.assertFalse(patient.blockchain_registered)
        self.assertEqual(patient.registration_tx_hash, '')
        self.assertIsNotNone(patient.created_at)
        self.assertIsNotNone(patient.updated_at)
    
    def test_blockchain_id_uniqueness(self):
        """Test blockchain_id unique constraint"""
        patient1 = Patient.objects.create(
            name="Patient One",
            age=30,
            gender="Male",
            branch=self.branch,
            blockchain_id="0x123abc"
        )
        
        # Creating another patient with same blockchain_id should fail
        with self.assertRaises(IntegrityError):
            Patient.objects.create(
                name="Patient Two",
                age=25,
                gender="Female",
                branch=self.branch,
                blockchain_id="0x123abc"
            )
    
    def test_generate_blockchain_id_success(self):
        """Test successful blockchain ID generation"""
        patient = Patient(
            name="Test Patient",
            date_of_birth=date(1990, 1, 1),
            contact_email="test@example.com"
        )
        blockchain_id = patient.generate_blockchain_id()
        
        self.assertIsNotNone(blockchain_id)
        self.assertTrue(blockchain_id.startswith("0x"))
        self.assertEqual(len(blockchain_id), 66)  # 0x + 64 hex chars
    
    def test_generate_blockchain_id_missing_data(self):
        """Test blockchain ID generation with missing required data"""
        # Missing date_of_birth
        patient1 = Patient(
            name="Test Patient",
            contact_email="test@example.com"
        )
        self.assertIsNone(patient1.generate_blockchain_id())
        
        # Missing contact_email
        patient2 = Patient(
            name="Test Patient",
            date_of_birth=date(1990, 1, 1)
        )
        self.assertIsNone(patient2.generate_blockchain_id())
    
    def test_generate_blockchain_id_deterministic(self):
        """Test that blockchain ID generation is deterministic"""
        patient1 = Patient(
            name="Test Patient",
            date_of_birth=date(1990, 1, 1),
            contact_email="test@example.com"
        )
        patient2 = Patient(
            name="Test Patient",
            date_of_birth=date(1990, 1, 1),
            contact_email="test@example.com"
        )
        
        id1 = patient1.generate_blockchain_id()
        id2 = patient2.generate_blockchain_id()
        
        self.assertEqual(id1, id2)
    
    def test_patient_timestamps(self):
        """Test patient timestamp fields"""
        before_creation = timezone.now()
        patient = Patient.objects.create(
            name="Time Test",
            age=30,
            gender="Male",
            branch=self.branch
        )
        after_creation = timezone.now()
        
        self.assertGreaterEqual(patient.created_at, before_creation)
        self.assertLessEqual(patient.created_at, after_creation)
        self.assertGreaterEqual(patient.updated_at, before_creation)
        self.assertLessEqual(patient.updated_at, after_creation)


class AppointmentModelTest(TestCase):
    """Test cases for Appointment model"""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Test",
            specialization="General",
            branch=self.branch
        )
        self.patient = Patient.objects.create(
            name="Test Patient",
            age=30,
            gender="Male",
            branch=self.branch
        )
    
    def test_appointment_creation(self):
        """Test basic appointment creation"""
        appointment_date = date.today() + timedelta(days=1)
        appointment_time = time(14, 30)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=appointment_date,
            time=appointment_time,
            branch=self.branch
        )
        
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.doctor, self.doctor)
        self.assertEqual(appointment.date, appointment_date)
        self.assertEqual(appointment.time, appointment_time)
        self.assertEqual(appointment.branch, self.branch)
    
    def test_appointment_str_representation(self):
        """Test string representation of appointment"""
        appointment_date = date.today() + timedelta(days=1)
        appointment = Appointment(
            patient=self.patient,
            doctor=self.doctor,
            date=appointment_date,
            time=time(14, 30)
        )
        
        expected_str = f"{self.patient.name} with {self.doctor.name} on {appointment_date}"
        self.assertEqual(str(appointment), expected_str)
    
    def test_appointment_relationships(self):
        """Test appointment foreign key relationships"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            branch=self.branch
        )
        
        # Test relationships work both ways
        self.assertEqual(appointment.patient.name, "Test Patient")
        self.assertEqual(appointment.doctor.name, "Dr. Test")
        self.assertEqual(appointment.branch.name, "Test Branch")
        
        # Test reverse relationships
        patient_appointments = self.patient.appointment_set.all()
        self.assertIn(appointment, patient_appointments)
        
        doctor_appointments = self.doctor.appointment_set.all()
        self.assertIn(appointment, doctor_appointments)