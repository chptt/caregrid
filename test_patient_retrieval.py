#!/usr/bin/env python
"""
Test patient retrieval endpoint
"""
import requests
import json

def test_patient_retrieval():
    """Test patient retrieval functionality"""
    base_url = "http://127.0.0.1:8000/api/patients/"
    
    print("Testing Patient Retrieval Endpoint...")
    print("=" * 50)
    
    # Test 1: Retrieve patient by database ID
    print("\n1. Testing retrieval by database ID...")
    response = requests.get(f"{base_url}1/")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Patient: {data['name']}")
        print(f"Blockchain ID: {data['blockchain_id']}")
        print(f"Appointments: {len(data['appointments'])} found")
        for apt in data['appointments']:
            print(f"  - {apt['date']} {apt['time']} with {apt['doctor']}")
        print("✅ Patient retrieval by ID successful!")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 2: Retrieve patient by blockchain ID
    print("\n2. Testing retrieval by blockchain ID...")
    blockchain_id = "0x9fa41a8e5cd768ff4404ed021eaff52a3d8a088798189c4a02f77b1e613e6ab3"
    response = requests.get(f"{base_url}{blockchain_id}/")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Patient: {data['name']}")
        print(f"Database ID: {data['id']}")
        print("✅ Patient retrieval by blockchain ID successful!")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 3: Test error handling with non-existent patient
    print("\n3. Testing error handling...")
    response = requests.get(f"{base_url}999/")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        data = response.json()
        print(f"Error message: {data['error']}")
        print("✅ Error handling working correctly!")
    else:
        print(f"❌ Unexpected response: {response.text}")
    
    # Test 4: Test error handling with invalid blockchain ID
    print("\n4. Testing error handling with invalid blockchain ID...")
    response = requests.get(f"{base_url}0xinvalid/")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        data = response.json()
        print(f"Error message: {data['error']}")
        print("✅ Error handling for invalid blockchain ID working correctly!")
    else:
        print(f"❌ Unexpected response: {response.text}")

if __name__ == "__main__":
    test_patient_retrieval()