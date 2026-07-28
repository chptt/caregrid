#!/usr/bin/env python
"""
Setup test data for patient registration and appointments
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caregrid.settings')
django.setup()

from core.models import Branch, Doctor

def setup_branches():
    """Create test branches if they don't exist"""
    if not Branch.objects.exists():
        Branch.objects.create(name='Main Hospital', location='Downtown Medical Center')
        Branch.objects.create(name='North Branch', location='North District Clinic')
        Branch.objects.create(name='South Branch', location='South Side Medical Center')
        print("✅ Created test branches")
    else:
        print("✅ Branches already exist")
    
    branches = Branch.objects.all()
    for branch in branches:
        print(f"  - {branch.id}: {branch.name} ({branch.location})")

def setup_doctors():
    """Create test doctors if they don't exist"""
    if not Doctor.objects.exists():
        branches = Branch.objects.all()
        if branches:
            main_hospital = branches.get(name='Main Hospital')
            north_branch = branches.get(name='North Branch')
            south_branch = branches.get(name='South Branch')
            
            # Main Hospital doctors
            Doctor.objects.create(name='Dr. Sarah Johnson', specialization='Cardiology', branch=main_hospital)
            Doctor.objects.create(name='Dr. Michael Chen', specialization='Neurology', branch=main_hospital)
            Doctor.objects.create(name='Dr. Emily Rodriguez', specialization='Pediatrics', branch=main_hospital)
            
            # North Branch doctors
            Doctor.objects.create(name='Dr. David Wilson', specialization='General Medicine', branch=north_branch)
            Doctor.objects.create(name='Dr. Lisa Thompson', specialization='Dermatology', branch=north_branch)
            
            # South Branch doctors
            Doctor.objects.create(name='Dr. James Brown', specialization='Orthopedics', branch=south_branch)
            Doctor.objects.create(name='Dr. Maria Garcia', specialization='Gynecology', branch=south_branch)
            
            print("✅ Created test doctors")
        else:
            print("❌ No branches found, cannot create doctors")
    else:
        print("✅ Doctors already exist")
    
    doctors = Doctor.objects.all()
    for doctor in doctors:
        print(f"  - {doctor.id}: {doctor.name} ({doctor.specialization}) at {doctor.branch.name}")

if __name__ == "__main__":
    print("Setting up test data...")
    setup_branches()
    setup_doctors()