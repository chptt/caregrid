"""Standardized API response helpers for consistent response formatting."""

from rest_framework.response import Response


def success_response(data=None, message=None, status_code=200):
    """Create a standardized success response."""
    payload = {}
    if message:
        payload['message'] = message
    if data:
        payload.update(data)
    return Response(payload, status=status_code)


def error_response(message, details=None, status_code=400):
    """Create a standardized error response."""
    payload = {
        'error': message,
        'status': 'error',
    }
    if details:
        payload['details'] = details
    return Response(payload, status=status_code)


def created_response(data=None, message='Resource created successfully'):
    """Create a standardized 201 response."""
    return success_response(data=data, message=message, status_code=201)


def not_found_response(message='Resource not found'):
    """Create a standardized 404 response."""
    return error_response(message, status_code=404)


def forbidden_response(message='Access denied'):
    """Create a standardized 403 response."""
    return error_response(message, status_code=403)


def unauthorized_response(message='Authentication required'):
    """Create a standardized 401 response."""
    return error_response(message, status_code=401)


def conflict_response(message='Resource already exists', details=None):
    """Create a standardized 409 response."""
    return error_response(message, details=details, status_code=409)
