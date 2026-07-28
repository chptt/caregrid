from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from web3 import Web3
import logging

from .models import Patient, Branch
from .serializers import PatientRegistrationSerializer, PatientSerializer
from .blockchain_service import BlockchainService
from .rate_limiting import rate_limit
from .permissions import (
    PatientRegistrationPermission,
    PatientAccessPermission,
    PatientSearchPermission,
    IsHealthcareStaff,
    check_branch_access,
    get_accessible_branches
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([PatientRegistrationPermission])
@rate_limit(limit_unauthenticated=10, window_seconds=60)  # 10 registrations per minute
def register_patient(request):
    """
    Register a new patient with blockchain integration.
    
    Creates a patient record, generates blockchain ID, and registers on blockchain.
    Requirements: 1.1, 1.2, 8.1
    """
    serializer = PatientRegistrationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create patient instance but don't save yet
            patient = Patient(**serializer.validated_data)
            
            # Check branch access for non-admin users
            if request.user.role != 'admin':
                # Ensure user can only register patients at their branch
                if hasattr(request.user, 'branch') and request.user.branch:
                    if patient.branch != request.user.branch:
                        return Response({
                            'error': 'Access denied',
                            'details': f'You can only register patients at your assigned branch: {request.user.branch.name}'
                        }, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({
                        'error': 'Access denied',
                        'details': 'You must be assigned to a branch to register patients'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Generate blockchain ID
            blockchain_id = patient.generate_blockchain_id()
            if not blockchain_id:
                return Response({
                    'error': 'Cannot generate blockchain ID',
                    'details': 'Date of birth and email are required for blockchain ID generation'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            patient.blockchain_id = blockchain_id
            
            # Check if patient already exists with this blockchain ID
            if Patient.objects.filter(blockchain_id=blockchain_id).exists():
                return Response({
                    'error': 'Patient already exists',
                    'details': 'A patient with this combination of name, date of birth, and email already exists',
                    'existing_blockchain_id': blockchain_id
                }, status=status.HTTP_409_CONFLICT)
            
            # Save patient to database first
            patient.save()
            
            # Register on blockchain
            blockchain_service = BlockchainService()
            patient_id_hash = Web3.keccak(text=blockchain_id)
            
            try:
                tx_hash, success = blockchain_service.register_patient(patient_id_hash)
                
                if success:
                    patient.blockchain_registered = True
                    patient.registration_tx_hash = tx_hash
                    patient.save()
                    
                    logger.info(f"Patient {patient.id} registered on blockchain with tx {tx_hash}")
                else:
                    logger.warning(f"Blockchain registration failed for patient {patient.id}")
                    # Continue with local registration even if blockchain fails
                    
            except Exception as e:
                logger.error(f"Blockchain registration error for patient {patient.id}: {e}")
                # Continue with local registration
            
            # Return success response
            response_serializer = PatientSerializer(patient)
            return Response({
                'message': 'Patient registered successfully',
                'patient': response_serializer.data,
                'blockchain_registered': patient.blockchain_registered
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Patient registration error: {e}")
        return Response({
            'error': 'Registration failed',
            'details': 'An internal error occurred during registration'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([PatientAccessPermission])
@rate_limit(limit_unauthenticated=100, window_seconds=60)  # 100 lookups per minute
def get_patient(request, patient_id):
    """
    Retrieve patient by ID or blockchain ID.
    
    Supports lookup by database ID or blockchain ID.
    Requirements: 1.3, 8.3
    """
    try:
        # Try to find by database ID first
        if patient_id.isdigit():
            try:
                patient = Patient.objects.get(id=int(patient_id))
            except Patient.DoesNotExist:
                return Response({
                    'error': 'Patient not found',
                    'details': f'No patient found with ID: {patient_id}'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Try to find by blockchain ID
            try:
                patient = Patient.objects.get(blockchain_id=patient_id)
            except Patient.DoesNotExist:
                return Response({
                    'error': 'Patient not found',
                    'details': f'No patient found with blockchain ID: {patient_id}'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Check branch access for non-admin users
        if not check_branch_access(request.user, patient):
            return Response({
                'error': 'Access denied',
                'details': 'You do not have permission to access this patient record'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PatientSerializer(patient)
        
        # Include appointment history
        appointments = patient.appointment_set.all().order_by('-date', '-time')
        appointment_data = []
        
        for appointment in appointments:
            appointment_data.append({
                'id': appointment.id,
                'doctor': appointment.doctor.name,
                'doctor_specialization': appointment.doctor.specialization,
                'date': appointment.date,
                'time': appointment.time,
                'branch': appointment.branch.name
            })
        
        response_data = serializer.data
        response_data['appointments'] = appointment_data
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Patient retrieval error: {e}")
        return Response({
            'error': 'Retrieval failed',
            'details': 'An internal error occurred during patient lookup'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([PatientSearchPermission])
@rate_limit(limit_unauthenticated=50, window_seconds=60)  # 50 searches per minute
def search_patients(request):
    """
    Search patients by name, email, or blockchain ID.
    
    Supports partial name matching and exact email/blockchain ID matching.
    Requirements: 8.3, 8.4
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response({
            'error': 'Search query required',
            'details': 'Please provide a search query parameter "q"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(query) < 2:
        return Response({
            'error': 'Query too short',
            'details': 'Search query must be at least 2 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get accessible branches for the user
        accessible_branches = get_accessible_branches(request.user)
        
        patients = Patient.objects.none()
        
        # Search by blockchain ID (exact match)
        if query.startswith('0x') and len(query) == 66:
            patients = Patient.objects.filter(
                blockchain_id=query,
                branch__in=accessible_branches
            )
        
        # Search by email (exact match)
        elif '@' in query:
            patients = Patient.objects.filter(
                contact_email__iexact=query,
                branch__in=accessible_branches
            )
        
        # Search by name (partial match)
        else:
            patients = Patient.objects.filter(
                name__icontains=query,
                branch__in=accessible_branches
            )
        
        # Limit results to prevent abuse
        patients = patients[:20]
        
        serializer = PatientSerializer(patients, many=True)
        
        return Response({
            'count': len(serializer.data),
            'patients': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Patient search error: {e}")
        return Response({
            'error': 'Search failed',
            'details': 'An internal error occurred during search'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsHealthcareStaff])
@rate_limit(limit_unauthenticated=20, window_seconds=60)  # 20 requests per minute
def get_branches(request):
    """
    Get list of all available branches for patient registration.
    """
    try:
        # Get accessible branches for the user
        accessible_branches = get_accessible_branches(request.user)
        
        branch_data = [
            {
                'id': branch.id,
                'name': branch.name,
                'location': branch.location
            }
            for branch in accessible_branches
        ]
        
        return Response({
            'branches': branch_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Branch retrieval error: {e}")
        return Response({
            'error': 'Failed to retrieve branches',
            'details': 'An internal error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)