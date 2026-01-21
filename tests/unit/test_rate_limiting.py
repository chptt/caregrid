"""
Unit tests for rate limiting functionality.
Tests the @rate_limit decorator and related utilities.
"""

import time
from unittest.mock import Mock, patch
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.rate_limiting import rate_limit, get_client_ip, get_rate_limit_status

User = get_user_model()


class RateLimitingTestCase(TestCase):
    """Test cases for rate limiting decorator and utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
    
    def test_get_client_ip_with_forwarded_header(self):
        """Test IP extraction with X-Forwarded-For header."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.100, 10.0.0.1'
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.100')
    
    def test_get_client_ip_without_forwarded_header(self):
        """Test IP extraction without X-Forwarded-For header."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.200'
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.200')
    
    def test_rate_limit_decorator_allows_under_limit(self):
        """Test that requests under the rate limit are allowed."""
        @rate_limit(limit_unauthenticated=10, limit_authenticated=20)
        def test_view(request):
            return JsonResponse({'status': 'ok'})
        
        # Create unauthenticated request
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        # Should allow first few requests
        for i in range(5):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_decorator_blocks_over_limit(self):
        """Test that requests over the rate limit are blocked."""
        @rate_limit(limit_unauthenticated=3, limit_authenticated=10)
        def test_view(request):
            return JsonResponse({'status': 'ok'})
        
        # Create unauthenticated request
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.META['REMOTE_ADDR'] = '192.168.1.101'
        
        # First 3 requests should be allowed
        for i in range(3):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
        
        # 4th request should be blocked
        response = test_view(request)
        self.assertEqual(response.status_code, 429)
        self.assertIn('Rate limit exceeded', response.content.decode())
        self.assertIn('Retry-After', response)
    
    def test_rate_limit_different_limits_for_auth_users(self):
        """Test that authenticated users get higher rate limits."""
        @rate_limit(limit_unauthenticated=2, limit_authenticated=5)
        def test_view(request):
            return JsonResponse({'status': 'ok'})
        
        # Test unauthenticated user
        request_unauth = self.factory.get('/')
        request_unauth.user = Mock()
        request_unauth.user.is_authenticated = False
        request_unauth.META['REMOTE_ADDR'] = '192.168.1.102'
        
        # Should allow 2 requests, block 3rd
        for i in range(2):
            response = test_view(request_unauth)
            self.assertEqual(response.status_code, 200)
        
        response = test_view(request_unauth)
        self.assertEqual(response.status_code, 429)
        
        # Test authenticated user
        request_auth = self.factory.get('/')
        request_auth.user = self.user
        
        # Should allow 5 requests
        for i in range(5):
            response = test_view(request_auth)
            self.assertEqual(response.status_code, 200)
        
        # 6th request should be blocked
        response = test_view(request_auth)
        self.assertEqual(response.status_code, 429)
    
    def test_get_rate_limit_status(self):
        """Test rate limit status reporting."""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.META['REMOTE_ADDR'] = '192.168.1.103'
        
        # Get initial status
        status = get_rate_limit_status(request)
        
        self.assertIn('limit', status)
        self.assertIn('remaining', status)
        self.assertIn('reset_time', status)
        self.assertIn('window_seconds', status)
        
        # Should have full limit remaining initially
        self.assertEqual(status['remaining'], status['limit'])
    
    @patch('core.rate_limiting.cache')
    def test_rate_limit_violation_tracking(self, mock_cache):
        """Test that rate limit violations are tracked for threat scoring."""
        @rate_limit(limit_unauthenticated=1)
        def test_view(request):
            return JsonResponse({'status': 'ok'})
        
        # Mock cache to simulate rate limit exceeded
        mock_cache.get.return_value = [time.time()]  # One request already in history
        
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.META['REMOTE_ADDR'] = '192.168.1.104'
        
        # This should trigger rate limit violation
        response = test_view(request)
        self.assertEqual(response.status_code, 429)
        
        # Verify that violation tracking was called
        # (This tests the integration with threat scoring)
        self.assertTrue(mock_cache.set.called)
    
    def test_rate_limit_with_custom_window(self):
        """Test rate limiting with custom time window."""
        @rate_limit(limit_unauthenticated=2, window_seconds=30)
        def test_view(request):
            return JsonResponse({'status': 'ok'})
        
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        request.META['REMOTE_ADDR'] = '192.168.1.105'
        
        # Should allow 2 requests
        for i in range(2):
            response = test_view(request)
            self.assertEqual(response.status_code, 200)
        
        # 3rd request should be blocked
        response = test_view(request)
        self.assertEqual(response.status_code, 429)
    
    def test_rate_limit_separate_tracking_per_ip(self):
        """Test that different IPs are tracked separately."""
        @rate_limit(limit_unauthenticated=2)
        def test_view(request):
            return JsonResponse({'status': 'ok'})
        
        # First IP
        request1 = self.factory.get('/')
        request1.user = Mock()
        request1.user.is_authenticated = False
        request1.META['REMOTE_ADDR'] = '192.168.1.106'
        
        # Second IP
        request2 = self.factory.get('/')
        request2.user = Mock()
        request2.user.is_authenticated = False
        request2.META['REMOTE_ADDR'] = '192.168.1.107'
        
        # Each IP should get its own rate limit
        for i in range(2):
            response1 = test_view(request1)
            response2 = test_view(request2)
            self.assertEqual(response1.status_code, 200)
            self.assertEqual(response2.status_code, 200)
        
        # Both should be blocked on 3rd request
        response1 = test_view(request1)
        response2 = test_view(request2)
        self.assertEqual(response1.status_code, 429)
        self.assertEqual(response2.status_code, 429)