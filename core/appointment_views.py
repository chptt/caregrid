from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
import logging
from datetime import datetime, date

from .models import Appointment, Patient, Doctor, Branch
from .serializers import AppointmentSerializer, DoctorSerializer
from .rate_limiting import rate_limit

logger = logging.getLogger(__name__)


@api_view(['POST'])
@rate_limit(limit_unauthenticated=20, window_seconds=60)  # 20 appointments per minute
def create_appointment(request):
    """
    Create a new appointment.
    
    Associates appointment with patient using universal patient ID.
    Requirements: 8.2
    """
    serializer = AppointmentSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create appointment
            appointment = serializer.save()
            
            logger.info(f"Appointment {appointment.id} created for patient {appointment.patient.blockchain_id}")
            
            # Return success response with full appointment details
            response_serializer = AppointmentSerializer(appointment)
            return Response({
                'message': 'Appointment created successfully',
                'appointment': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Appointment creation error: {e}")
        return Response({
            'error': 'Appointment creation failed',
            'details': 'An internal error occurred during appointment creation'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit(limit_unauthenticated=100, window_seconds=60)  # 100 requests per minute
def list_appointments(request):
    """
    List appointments with optional filtering.
    
    Supports filtering by patient_id, patient_blockchain_id, doctor_id, branch_id, and date.
    Requirements: 8.2
    """
    try:
        appointments = Appointment.objects.all()
        
        # Filter by patient ID (database ID)
        patient_id = request.GET.get('patient_id')
        if patient_id:
            if patient_id.isdigit():
                appointments = appointments.filter(patient_id=int(patient_id))
            else:
                return Response({
                    'error': 'Invalid patient_id',
                    'details': 'patient_id must be a numeric value'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter by patient blockchain ID
        patient_blockchain_id = request.GET.get('patient_blockchain_id')
        if patient_blockchain_id:
            appointments = appointments.filter(patient__blockchain_id=patient_blockchain_id)
        
        # Filter by doctor ID
        doctor_id = request.GET.get('doctor_id')
        if doctor_id:
            if doctor_id.isdigit():
                appointments = appointments.filter(doctor_id=int(doctor_id))
            else:
                return Response({
                    'error': 'Invalid doctor_id',
                    'details': 'doctor_id must be a numeric value'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter by branch ID
        branch_id = request.GET.get('branch_id')
        if branch_id:
            if branch_id.isdigit():
                appointments = appointments.filter(branch_id=int(branch_id))
            else:
                return Response({
                    'error': 'Invalid branch_id',
                    'details': 'branch_id must be a numeric value'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter by date
        appointment_date = request.GET.get('date')
        if appointment_date:
            try:
                parsed_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                appointments = appointments.filter(date=parsed_date)
            except ValueError:
                return Response({
                    'error': 'Invalid date format',
                    'details': 'Date must be in YYYY-MM-DD format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter by date range
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            try:
                parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
                appointments = appointments.filter(date__gte=parsed_start)
            except ValueError:
                return Response({
                    'error': 'Invalid start_date format',
                    'details': 'start_date must be in YYYY-MM-DD format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if end_date:
            try:
                parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
                appointments = appointments.filter(date__lte=parsed_end)
            except ValueError:
                return Response({
                    'error': 'Invalid end_date format',
                    'details': 'end_date must be in YYYY-MM-DD format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Order by date and time (most recent first)
        appointments = appointments.order_by('-date', '-time')
        
        # Limit results to prevent abuse
        limit = request.GET.get('limit', '50')
        try:
            limit = int(limit)
            if limit > 100:
                limit = 100
            appointments = appointments[:limit]
        except ValueError:
            appointments = appointments[:50]
        
        serializer = AppointmentSerializer(appointments, many=True)
        
        return Response({
            'count': len(serializer.data),
            'appointments': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Appointment listing error: {e}")
        return Response({
            'error': 'Failed to retrieve appointments',
            'details': 'An internal error occurred during appointment retrieval'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit(limit_unauthenticated=50, window_seconds=60)  # 50 requests per minute
def get_appointment(request, appointment_id):
    """
    Retrieve a specific appointment by ID.
    """
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        serializer = AppointmentSerializer(appointment)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Appointment.DoesNotExist:
        return Response({
            'error': 'Appointment not found',
            'details': f'No appointment found with ID: {appointment_id}'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Appointment retrieval error: {e}")
        return Response({
            'error': 'Retrieval failed',
            'details': 'An internal error occurred during appointment lookup'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit(limit_unauthenticated=30, window_seconds=60)  # 30 requests per minute
def get_doctors(request):
    """
    Get list of all available doctors, optionally filtered by branch.
    """
    try:
        doctors = Doctor.objects.all()
        
        # Filter by branch if specified
        branch_id = request.GET.get('branch_id')
        if branch_id:
            if branch_id.isdigit():
                doctors = doctors.filter(branch_id=int(branch_id))
            else:
                return Response({
                    'error': 'Invalid branch_id',
                    'details': 'branch_id must be a numeric value'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        doctors = doctors.order_by('name')
        serializer = DoctorSerializer(doctors, many=True)
        
        return Response({
            'doctors': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Doctor retrieval error: {e}")
        return Response({
            'error': 'Failed to retrieve doctors',
            'details': 'An internal error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@rate_limit(limit_unauthenticated=100, window_seconds=60)  # 100 requests per minute
def get_patient_appointments(request, patient_id):
    """
    Get all appointments for a specific patient.
    Supports lookup by database ID or blockchain ID.
    """
    try:
        # Try to find patient by database ID first
        if patient_id.isdigit():
            patient = get_object_or_404(Patient, id=int(patient_id))
        else:
            # Try to find by blockchain ID
            patient = get_object_or_404(Patient, blockchain_id=patient_id)
        
        appointments = Appointment.objects.filter(patient=patient).order_by('-date', '-time')
        
        # Apply date filtering if provided
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
                appointments = appointments.filter(date__gte=parsed_start)
            except ValueError:
                return Response({
                    'error': 'Invalid start_date format',
                    'details': 'start_date must be in YYYY-MM-DD format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if end_date:
            try:
                parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
                appointments = appointments.filter(date__lte=parsed_end)
            except ValueError:
                return Response({
                    'error': 'Invalid end_date format',
                    'details': 'end_date must be in YYYY-MM-DD format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AppointmentSerializer(appointments, many=True)
        
        return Response({
            'patient_id': patient.id,
            'patient_blockchain_id': patient.blockchain_id,
            'patient_name': patient.name,
            'count': len(serializer.data),
            'appointments': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Patient.DoesNotExist:
        return Response({
            'error': 'Patient not found',
            'details': f'No patient found with ID: {patient_id}'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Patient appointments retrieval error: {e}")
        return Response({
            'error': 'Retrieval failed',
            'details': 'An internal error occurred during appointment lookup'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)