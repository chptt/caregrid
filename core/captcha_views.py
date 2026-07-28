"""
CAPTCHA API views for SecurityMiddleware integration.
Provides endpoints for generating and verifying CAPTCHA challenges.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json

from .middleware import SecurityMiddleware

logger = logging.getLogger('security')


@method_decorator(csrf_exempt, name='dispatch')
class CaptchaView(View):
    """
    API view for CAPTCHA generation and verification.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize SecurityMiddleware to access CAPTCHA methods
        self.security_middleware = SecurityMiddleware(None)
    
    def get(self, request):
        """
        Generate a new CAPTCHA challenge.
        
        Returns:
            JSON response with CAPTCHA token and challenge
        """
        try:
            # Get client IP
            ip_address = self._get_client_ip(request)
            
            # Generate CAPTCHA
            captcha_data = self.security_middleware.generate_captcha_token(ip_address)
            
            if 'error' in captcha_data:
                return JsonResponse(captcha_data, status=500)
            
            return JsonResponse({
                'success': True,
                'captcha': captcha_data,
                'message': 'CAPTCHA generated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error generating CAPTCHA: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate CAPTCHA'
            }, status=500)
    
    def post(self, request):
        """
        Verify CAPTCHA answer.
        
        Expected POST data:
        {
            "token": "captcha_token",
            "answer": "user_answer"
        }
        
        Returns:
            JSON response with verification result
        """
        try:
            # Parse request data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            token = data.get('token')
            answer = data.get('answer')
            
            if not token or not answer:
                return JsonResponse({
                    'success': False,
                    'error': 'Token and answer are required'
                }, status=400)
            
            # Get client IP
            ip_address = self._get_client_ip(request)
            
            # Verify CAPTCHA answer
            is_valid = self.security_middleware.verify_captcha_answer(token, answer, ip_address)
            
            if is_valid:
                return JsonResponse({
                    'success': True,
                    'message': 'CAPTCHA verified successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid CAPTCHA answer'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error verifying CAPTCHA: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to verify CAPTCHA'
            }, status=500)
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


@require_http_methods(["GET"])
def captcha_status(request):
    """
    Get CAPTCHA status for current IP.
    
    Returns:
        JSON response with CAPTCHA requirement status
    """
    try:
        # Initialize middleware to access threat calculation
        security_middleware = SecurityMiddleware(None)
        
        # Get client IP
        ip_address = security_middleware._get_client_ip(request)
        
        # Calculate current threat score
        threat_score, factors = security_middleware.threat_calculator.calculate_threat_score(request, ip_address)
        
        # Determine if CAPTCHA is required
        requires_captcha = security_middleware.threat_calculator.should_require_captcha(threat_score)
        
        return JsonResponse({
            'ip_address': ip_address,
            'threat_score': threat_score,
            'requires_captcha': requires_captcha,
            'threat_factors': factors
        })
        
    except Exception as e:
        logger.error(f"Error getting CAPTCHA status: {e}")
        return JsonResponse({
            'error': 'Failed to get CAPTCHA status'
        }, status=500)