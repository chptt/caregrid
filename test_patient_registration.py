#!/usr/bin/env python
"""
Simple test script for patient registration endpoint
"""
import requests
import json
from datetime import date

# Test data
test_patient = {
    "name": "John Doe",
    "date_of_birth": "1990-05-15",
    "gender": "M",
    "contact_phone": "+1234567890",
    "contact_email": "john.doe@example.com",
    "address": "123 Main Street, City, State 12345",
    "branch": 1
}

def test_patient_registration():
    """Test patient registration endpoint"""
    url = "http://127.0.0.1:8000/api/patients/"
    
    try:
        response = requests.post(url, json=test_patient)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Patient registration successful!")
            return response.json()
        else:
            print("❌ Patient registration failed!")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django is running on port 8000.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_get_patient(patient_id):
    """Test patient retrieval endpoint"""
    url = f"http://127.0.0.1:8000/api/patients/{patient_id}/"
    
    try:
        response = requests.get(url)
        print(f"\nGET Patient - Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Patient retrieval successful!")
        else:
            print("❌ Patient retrieval failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_branches():
    """Test branches endpoint"""
    url = "http://127.0.0.1:8000/api/branches/"
    
    try:
        response = requests.get(url)
        print(f"\nGET Branches - Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Branches retrieval successful!")
        else:
            print("❌ Branches retrieval failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing Patient Registration API...")
    print("=" * 50)
    
    # Test branches first
    test_get_branches()
    
    # Test patient registration
    result = test_patient_registration()
    
    # Test patient retrieval if registration was successful
    if result and 'patient' in result:
        patient_id = result['patient']['id']
        blockchain_id = result['patient']['blockchain_id']
        
        # Test retrieval by database ID
        test_get_patient(patient_id)
        
        # Test retrieval by blockchain ID
        if blockchain_id:
            test_get_patient(blockchain_id)