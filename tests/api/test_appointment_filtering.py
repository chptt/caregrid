#!/usr/bin/env python
"""
Test appointment filtering functionality
"""
import requests
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caregrid.settings')
django.setup()

from core.models import Patient

BASE_URL = 'http://127.0.0.1:8000'

def test_filter_by_blockchain_id():
    """Test filtering appointments by patient blockchain ID"""
    print("Testing appointment filtering by blockchain ID")
    
    patient = Patient.objects.first()
    if not patient or not patient.blockchain_id:
        print("❌ No patient with blockchain ID found")
        return
    
    print(f"Testing with blockchain ID: {patient.blockchain_id}")
    
    try:
        response = requests.get(f'{BASE_URL}/api/appointments/list/?patient_blockchain_id={patient.blockchain_id}')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} appointments for blockchain ID:")
            for appointment in data['appointments']:
                print(f"  - {appointment['id']}: {appointment['patient_name']} with {appointment['doctor_name']} on {appointment['date']}")
                print(f"    Blockchain ID: {appointment['patient_blockchain_id']}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_filter_by_date():
    """Test filtering appointments by date"""
    print("\nTesting appointment filtering by date")
    
    try:
        response = requests.get(f'{BASE_URL}/api/appointments/list/?date=2026-01-20')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} appointments for 2026-01-20:")
            for appointment in data['appointments']:
                print(f"  - {appointment['id']}: {appointment['patient_name']} with {appointment['doctor_name']} on {appointment['date']}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_filter_by_blockchain_id()
    test_filter_by_date()