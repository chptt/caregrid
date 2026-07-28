#!/usr/bin/env python
"""
Test single appointment endpoint
"""
import requests

BASE_URL = 'http://127.0.0.1:8000'

def test_get_single_appointment():
    """Test getting a single appointment"""
    print("Testing GET /api/appointments/2/")
    
    try:
        response = requests.get(f'{BASE_URL}/api/appointments/2/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Appointment retrieved successfully:")
            print(f"  - ID: {data['id']}")
            print(f"  - Patient: {data['patient_name']} (ID: {data['patient_blockchain_id']})")
            print(f"  - Doctor: {data['doctor_name']} ({data['doctor_specialization']})")
            print(f"  - Date/Time: {data['date']} at {data['time']}")
            print(f"  - Branch: {data['branch_name']}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_get_single_appointment()