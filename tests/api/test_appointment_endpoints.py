#!/usr/bin/env python
"""
Test script for appointment endpoints
"""
import os
import sys
import django
import requests
import json
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caregrid.settings')
django.setup()

from core.models import Patient, Doctor, Branch

BASE_URL = 'http://127.0.0.1:8000'

def test_get_doctors():
    """Test getting list of doctors"""
    print("\n=== Testing GET /api/doctors/ ===")
    
    try:
        response = requests.get(f'{BASE_URL}/api/doctors/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data['doctors'])} doctors:")
            for doctor in data['doctors']:
                print(f"  - {doctor['id']}: {doctor['name']} ({doctor['specialization']}) at {doctor['branch_name']}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Django server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_create_appointment():
    """Test creating an appointment"""
    print("\n=== Testing POST /api/appointments/ ===")
    
    # Get first patient and doctor
    patient = Patient.objects.first()
    doctor = Doctor.objects.first()
    
    if not patient or not doctor:
        print("❌ No patient or doctor found in database")
        return False
    
    if not patient.blockchain_id:
        print("❌ Patient has no blockchain ID")
        return False
    
    appointment_data = {
        'patient': patient.id,
        'doctor': doctor.id,
        'date': str(date.today() + timedelta(days=1)),  # Tomorrow
        'time': '10:00:00',
        'branch': doctor.branch.id
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/appointments/',
            json=appointment_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Appointment created successfully:")
            appointment = data['appointment']
            print(f"  - ID: {appointment['id']}")
            print(f"  - Patient: {appointment['patient_name']} (ID: {appointment['patient_blockchain_id']})")
            print(f"  - Doctor: {appointment['doctor_name']} ({appointment['doctor_specialization']})")
            print(f"  - Date/Time: {appointment['date']} at {appointment['time']}")
            print(f"  - Branch: {appointment['branch_name']}")
            return appointment['id']
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Django server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return False

def test_list_appointments():
    """Test listing appointments"""
    print("\n=== Testing GET /api/appointments/list/ ===")
    
    try:
        response = requests.get(f'{BASE_URL}/api/appointments/list/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['count']} appointments:")
            for appointment in data['appointments']:
                print(f"  - {appointment['id']}: {appointment['patient_name']} with {appointment['doctor_name']} on {appointment['date']}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Django server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_get_patient_appointments():
    """Test getting appointments for a specific patient"""
    print("\n=== Testing GET /api/appointments/patient/{patient_id}/ ===")
    
    patient = Patient.objects.first()
    if not patient:
        print("❌ No patient found in database")
        return False
    
    try:
        # Test with database ID
        response = requests.get(f'{BASE_URL}/api/appointments/patient/{patient.id}/')
        print(f"Status (DB ID): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['count']} appointments for {data['patient_name']}:")
            for appointment in data['appointments']:
                print(f"  - {appointment['id']}: with {appointment['doctor_name']} on {appointment['date']}")
        
        # Test with blockchain ID if available
        if patient.blockchain_id:
            response = requests.get(f'{BASE_URL}/api/appointments/patient/{patient.blockchain_id}/')
            print(f"Status (Blockchain ID): {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Found {data['count']} appointments using blockchain ID")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Django server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def main():
    print("Testing Appointment Endpoints")
    print("=" * 40)
    
    # Check if we have test data
    patient_count = Patient.objects.count()
    doctor_count = Doctor.objects.count()
    branch_count = Branch.objects.count()
    
    print(f"Database status:")
    print(f"  - Patients: {patient_count}")
    print(f"  - Doctors: {doctor_count}")
    print(f"  - Branches: {branch_count}")
    
    if patient_count == 0 or doctor_count == 0 or branch_count == 0:
        print("\n❌ Missing test data. Please run setup_test_data.py and register some patients first.")
        return
    
    # Run tests
    if not test_get_doctors():
        return
    
    appointment_id = test_create_appointment()
    test_list_appointments()
    test_get_patient_appointments()
    
    print("\n✅ All appointment endpoint tests completed!")

if __name__ == "__main__":
    main()