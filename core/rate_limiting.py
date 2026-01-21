"""
Rate limiting decorator and utilities for CareGrid API endpoints.
Implements distributed rate limiting using Redis with different limits
for authenticated and unauthenticated users.
"""

import time
import functools
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta


def get_client_ip(request):
    """Extract client IP address from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def rate_limit(limit_unauthenticated=None, limit_authenticated=None, window_seconds=60):
    """
    Rate limiting decorator for Django views.
    
    Args:
        limit_unauthenticated: Requests per window for unauthenticated users
        limit_authenticated: Requests per window for authenticated users  
        window_seconds: Time window in seconds (default: 60 seconds)
    
    Uses Redis for distributed rate limiting across multiple server instances.
    Returns HTTP 429 when rate limit is exceeded with Retry-After header.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get rate limits from settings if not specified
            if limit_unauthenticated is None:
                unauthenticated_limit = getattr(settings, 'RATE_LIMITS', {}).get('UNAUTHENTICATED', 100)
            else:
                unauthenticated_limit = limit_unauthenticated
                
            if limit_authenticated is None:
                authenticated_limit = getattr(settings, 'RATE_LIMITS', {}).get('AUTHENTICATED', 500)
            else:
                authenticated_limit = limit_authenticated
            
            # Determine which limit to use
            if request.user.is_authenticated:
                rate_limit_value = authenticated_limit
                user_key = f"user:{request.user.id}"
            else:
                rate_limit_value = unauthenticated_limit
                ip_address = get_client_ip(request)
                user_key = f"ip:{ip_address}"
            
            # Create Redis key for rate limiting
            cache_key = f"rate_limit:{user_key}:{window_seconds}"
            
            # Get current request count and timestamp
            now = time.time()
            window_start = now - window_seconds
            
            # Get existing request history
            request_history = cache.get(cache_key, [])
            
            # Filter out requests outside the current window
            request_history = [timestamp for timestamp in request_history if timestamp > window_start]
            
            # Check if rate limit is exceeded
            if len(request_history) >= rate_limit_value:
                # Calculate retry-after time (seconds until oldest request expires)
                oldest_request = min(request_history)
                retry_after = int(oldest_request + window_seconds - now) + 1
                
                # Increase threat score for repeat violations
                _increase_threat_score_for_rate_limit_violation(request, user_key)
                
                # Return 429 with Retry-After header
                response = JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {rate_limit_value} per {window_seconds} seconds',
                    'retry_after': retry_after
                }, status=429)
                response['Retry-After'] = str(retry_after)
                return response
            
            # Add current request to history
            request_history.append(now)
            
            # Store updated history in cache
            cache.set(cache_key, request_history, timeout=window_seconds + 10)
            
            # Call the original view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def _increase_threat_score_for_rate_limit_violation(request, user_key):
    """
    Increase threat score for users who repeatedly violate rate limits.
    This helps identify potential attackers who are testing rate limits.
    Requirements 10.5: Increase threat score for repeat violations.
    """
    from .threat_calculator import get_threat_calculator
    import redis
    
    # Use Redis directly for violation tracking
    redis_client = redis.Redis(
        host=getattr(settings, 'REDIS_HOST', 'localhost'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_DB', 0),
        decode_responses=True
    )
    
    violation_key = f"rate_violations:{user_key}"
    
    # Track rate limit violations
    violations = redis_client.incr(violation_key)
    redis_client.expire(violation_key, 3600)  # Track for 1 hour
    
    # If this is an IP-based violation, increase threat score
    if user_key.startswith('ip:'):
        ip_address = user_key.split(':', 1)[1]
        threat_key = f"threat_boost:{ip_address}"
        
        # Add threat score boost based on number of violations
        # Requirements 10.5: Increase threat score for repeat violations
        if violations >= 5:
            threat_boost = 15  # Significant boost for repeated violations
        elif violations >= 3:
            threat_boost = 10
        else:
            threat_boost = 5
        
        redis_client.setex(threat_key, 1800, threat_boost)  # 30 minutes
        
        # Log the violation for security monitoring
        import logging
        logger = logging.getLogger('security')
        logger.warning(f"Rate limit violation #{violations} for IP {ip_address}, threat boost: {threat_boost}")
        
        # If violations are excessive, consider this a potential attack
        if violations >= 10:
            logger.error(f"Excessive rate limit violations ({violations}) from IP {ip_address} - potential attack")
            
            # Optionally trigger additional security measures
            threat_calculator = get_threat_calculator()
            # This could trigger auto-blocking if integrated with SecurityMiddleware


def get_rate_limit_threat_boost(ip_address):
    """
    Get threat score boost for IP addresses that have violated rate limits.
    This is used by the threat calculator to increase scores for repeat offenders.
    """
    threat_key = f"threat_boost:{ip_address}"
    return cache.get(threat_key, 0)


def reset_rate_limit(user_key):
    """
    Reset rate limit for a specific user or IP.
    Useful for administrative functions.
    """
    cache_pattern = f"rate_limit:{user_key}:*"
    # Note: Redis doesn't support pattern deletion in Django cache
    # This would need to be implemented with direct Redis commands if needed
    pass


def get_rate_limit_status(request, window_seconds=60):
    """
    Get current rate limit status for a user/IP.
    Returns remaining requests and reset time.
    """
    if request.user.is_authenticated:
        rate_limit_value = getattr(settings, 'RATE_LIMITS', {}).get('AUTHENTICATED', 500)
        user_key = f"user:{request.user.id}"
    else:
        rate_limit_value = getattr(settings, 'RATE_LIMITS', {}).get('UNAUTHENTICATED', 100)
        ip_address = get_client_ip(request)
        user_key = f"ip:{ip_address}"
    
    cache_key = f"rate_limit:{user_key}:{window_seconds}"
    
    now = time.time()
    window_start = now - window_seconds
    
    request_history = cache.get(cache_key, [])
    request_history = [timestamp for timestamp in request_history if timestamp > window_start]
    
    remaining = max(0, rate_limit_value - len(request_history))
    
    if request_history:
        reset_time = min(request_history) + window_seconds
    else:
        reset_time = now + window_seconds
    
    return {
        'limit': rate_limit_value,
        'remaining': remaining,
        'reset_time': reset_time,
        'window_seconds': window_seconds
    }