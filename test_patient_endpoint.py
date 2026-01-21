#!/usr/bin/env python
"""
Test patient registration endpoint using Django test client
"""
import os
import sys
import django
import json
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caregrid.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from core.models import Branch, Patient

def test_patient_registration():
    """Test patient registration endpoint"""
    client = Client()
    
    # Ensure we have a branch
    branch, created = Branch.objects.get_or_create(
        name='Test Hospital',
        defaults={'location': 'Test City'}
    )
    
    # Test data
    patient_data = {
        "name": "John Doe",
        "date_of_birth": "1990-05-15",
        "gender": "M",
        "contact_phone": "+1234567890",
        "contact_email": "john.doe@example.com",
        "address": "123 Main Street, City, State 12345",
        "branch": branch.id
    }
    
    print("Testing patient registration...")
    print(f"Test data: {json.dumps(patient_data, indent=2)}")
    
    # Test POST to patient registration endpoint
    response = client.post(
        '/api/patients/',
        data=json.dumps(patient_data),
        content_type='application/json'
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 201:
            print("✅ Patient registration successful!")
            
            # Test retrieval
            patient_id = response_data['patient']['id']
            blockchain_id = response_data['patient']['blockchain_id']
            
            print(f"\nTesting patient retrieval by ID: {patient_id}")
            get_response = client.get(f'/api/patients/{patient_id}/')
            print(f"GET Response Status: {get_response.status_code}")
            
            if get_response.status_code == 200:
                print("✅ Patient retrieval by ID successful!")
                print(f"Retrieved: {get_response.json()['name']}")
            
            # Test retrieval by blockchain ID
            if blockchain_id:
                print(f"\nTesting patient retrieval by blockchain ID: {blockchain_id}")
                blockchain_response = client.get(f'/api/patients/{blockchain_id}/')
                print(f"Blockchain GET Response Status: {blockchain_response.status_code}")
                
                if blockchain_response.status_code == 200:
                    print("✅ Patient retrieval by blockchain ID successful!")
        else:
            print("✅ Request processed successfully!")
    else:
        try:
            error_data = response.json()
            print(f"Error Response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Error Response: {response.content.decode()}")
        print("❌ Patient registration failed!")

def test_branches_endpoint():
    """Test branches endpoint"""
    client = Client()
    
    print("\nTesting branches endpoint...")
    response = client.get('/api/branches/')
    
    print(f"Branches Response Status: {response.status_code}")
    
    if response.status_code == 200:
        branches_data = response.json()
        print(f"Branches: {json.dumps(branches_data, indent=2)}")
        print("✅ Branches endpoint successful!")
    else:
        print("❌ Branches endpoint failed!")

def test_duplicate_registration():
    """Test duplicate patient registration"""
    client = Client()
    
    # Ensure we have a branch
    branch, created = Branch.objects.get_or_create(
        name='Test Hospital',
        defaults={'location': 'Test City'}
    )
    
    # Same test data as before
    patient_data = {
        "name": "John Doe",
        "date_of_birth": "1990-05-15",
        "gender": "M",
        "contact_phone": "+1234567890",
        "contact_email": "john.doe@example.com",
        "address": "123 Main Street, City, State 12345",
        "branch": branch.id
    }
    
    print("\nTesting duplicate patient registration...")
    
    # Try to register the same patient again
    response = client.post(
        '/api/patients/',
        data=json.dumps(patient_data),
        content_type='application/json'
    )
    
    print(f"Duplicate Registration Status: {response.status_code}")
    
    if response.status_code == 409:
        print("✅ Duplicate registration correctly rejected!")
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
    else:
        print("❌ Duplicate registration not handled correctly!")

if __name__ == "__main__":
    print("Testing Patient Registration API with Django Test Client")
    print("=" * 60)
    
    # Clean up any existing test patients
    Patient.objects.filter(contact_email="john.doe@example.com").delete()
    
    test_branches_endpoint()
    test_patient_registration()
    test_duplicate_registration()
    
    print("\n" + "=" * 60)
    print("Test completed!")