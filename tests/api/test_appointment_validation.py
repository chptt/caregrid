#!/usr/bin/env python
"""
Test appointment validation
"""
import requests
import json
from datetime import date, timedelta

BASE_URL = 'http://127.0.0.1:8000'

def test_invalid_appointment():
    """Test creating an appointment with invalid data"""
    print("Testing appointment validation")
    
    # Test 1: Past date
    print("\n1. Testing past date validation:")
    appointment_data = {
        'patient': 1,
        'doctor': 1,
        'date': str(date.today() - timedelta(days=1)),  # Yesterday
        'time': '10:00:00',
        'branch': 1
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/appointments/',
            json=appointment_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print("✅ Validation correctly rejected past date:")
            print(f"  Error: {data}")
        else:
            print(f"❌ Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Invalid patient ID
    print("\n2. Testing invalid patient ID:")
    appointment_data = {
        'patient': 999,  # Non-existent patient
        'doctor': 1,
        'date': str(date.today() + timedelta(days=1)),
        'time': '10:00:00',
        'branch': 1
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/appointments/',
            json=appointment_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print("✅ Validation correctly rejected invalid patient:")
            print(f"  Error: {data}")
        else:
            print(f"❌ Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_invalid_appointment()