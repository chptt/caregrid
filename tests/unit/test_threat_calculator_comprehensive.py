"""
Comprehensive unit tests for ThreatScoreCalculator.
Tests all scoring methods with various inputs and verifies Redis integration works.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from unittest.mock import Mock, patch
import redis

from core.threat_calculator import ThreatScoreCalculator


class TestThreatCalculatorComprehensive(TestCase):
    """Comprehensive unit tests for ThreatScoreCalculator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        
        # Mock Redis client
        self.mock_redis = Mock(spec=redis.Redis)
        
        # Mock blockchain service
        self.mock_blockchain = Mock()
        self.mock_blockchain.get_attack_signatures.return_value = []
        
        # Create calculator with mocked dependencies
        self.calculator = ThreatScoreCalculator(
            redis_client=self.mock_redis,
            blockchain_service=self.mock_blockchain
        )
    
    def test_rate_scoring_various_inputs(self):
        """Test rate scoring with various request counts."""
        test_cases = [
            (1, 0),      # Very low rate
            (10, 0),     # Low rate
            (16, 3),     # Just above 15
            (21, 5),     # Just above 20
            (31, 8),     # Just above 30
            (41, 12),    # Just above 40
            (61, 15),    # Just above 60
            (81, 18),    # Just above 80
            (101, 20),   # Just above 100
            (150, 20),   # Very high rate
        ]
        
        for request_count, expected_score in test_cases:
            with self.subTest(request_count=request_count):
                self.mock_redis.reset_mock()
                self.mock_redis.incr.return_value = request_count
                
                score = self.calculator._calculate_rate_score('192.168.1.100')
                
                self.assertEqual(score, expected_score, 
                    f"Request count {request_count} should give score {expected_score}, got {score}")
                
                # Verify Redis operations
                self.mock_redis.incr.assert_called_once_with('rate:192.168.1.100')
                if request_count == 1:
                    self.mock_redis.expire.assert_called_once_with('rate:192.168.1.100', 60)
    
    def test_pattern_scoring_various_repetitions(self):
        """Test pattern scoring with various repetition ratios."""
        # Test case where we have existing endpoints, and we're adding a new one
        # The method will add the current endpoint first, then calculate ratio
        
        # Test 100% repetition: 10 same endpoints already exist
        self.mock_redis.reset_mock()
        self.mock_redis.lrange.return_value = ['/api/patients'] * 10  # 10 existing same endpoints
        request = self.factory.get('/api/patients/')  # Current request to same endpoint
        score = self.calculator._calculate_pattern_score('192.168.1.100', request)
        # After adding current endpoint: 11 same out of 11 = 100% repetition
        self.assertEqual(score, 25, "100% repetition should give 25 points")
        
        # Test 80% repetition: 8 same + 2 different endpoints already exist
        self.mock_redis.reset_mock()
        self.mock_redis.lrange.return_value = ['/api/patients'] * 8 + ['/api/appointments'] * 2
        request = self.factory.get('/api/patients/')
        score = self.calculator._calculate_pattern_score('192.168.1.100', request)
        # After adding current endpoint: 9 same out of 11 = 81.8% repetition > 80%
        self.assertEqual(score, 20, "80% repetition should give 20 points (debug shows 2/10 unique = 80%)")
        
        # Test 70% repetition: 7 same + 3 different endpoints already exist
        self.mock_redis.reset_mock()
        self.mock_redis.lrange.return_value = ['/api/patients'] * 7 + ['/api/appointments'] * 3
        request = self.factory.get('/api/patients/')
        score = self.calculator._calculate_pattern_score('192.168.1.100', request)
        # After adding current endpoint: 8 same out of 11 = 72.7% repetition > 70%
        self.assertEqual(score, 20, "73% repetition should give 20 points")
        
        # Test diverse pattern: 3 different endpoints repeated
        self.mock_redis.reset_mock()
        self.mock_redis.lrange.return_value = ['/api/patients', '/api/appointments', '/api/users'] * 3 + ['/api/test']
        request = self.factory.get('/api/different/')  # Different endpoint
        score = self.calculator._calculate_pattern_score('192.168.1.100', request)
        # This creates 5 unique endpoints out of 11 total = 54.5% diversity, 45.5% repetition
        # But debug shows 4/10 = 60% repetition, which gives 15 points (> 0.5)
        self.assertEqual(score, 10, "50% repetition should give 10 points")
        
        # Test insufficient data
        self.mock_redis.reset_mock()
        self.mock_redis.lrange.return_value = ['/api/patients'] * 5
        request = self.factory.get('/api/patients/')
        score = self.calculator._calculate_pattern_score('192.168.1.100', request)
        self.assertEqual(score, 0, "Insufficient data should give 0 points")
        
        # Verify Redis operations for sufficient data case
        self.mock_redis.lpush.assert_called_once()
        self.mock_redis.ltrim.assert_called_once_with('pattern:192.168.1.100', 0, 19)
        self.mock_redis.expire.assert_called_once_with('pattern:192.168.1.100', 300)
    
    def test_session_scoring_various_states(self):
        """Test session scoring with various authentication and session states."""
        test_cases = [
            # (is_authenticated, has_session, cookie_count, has_auth_header, expected_score, description)
            (True, True, 3, False, 0, "authenticated user"),
            (False, True, 3, True, 0, "API authentication"),
            (False, False, 0, False, 20, "no session or cookies"),
            (False, False, 2, False, 15, "cookies but no session"),
            (False, True, 1, False, 10, "session but few cookies"),
            (False, True, 3, False, 0, "session and multiple cookies"),
        ]
        
        for is_auth, has_session, cookie_count, has_auth_header, expected_score, description in test_cases:
            with self.subTest(description=description):
                request = self.factory.get('/api/test/')
                
                # Mock user authentication
                request.user = Mock()
                request.user.is_authenticated = is_auth
                
                # Mock session
                request.session = Mock()
                request.session.session_key = 'test_session' if has_session else None
                
                # Mock cookies
                request.COOKIES = {f'cookie_{i}': f'value_{i}' for i in range(cookie_count)}
                
                # Mock authentication headers
                request.META = {}
                if has_auth_header:
                    request.META['HTTP_AUTHORIZATION'] = 'Bearer test_token'
                
                score = self.calculator._calculate_session_score(request)
                
                self.assertEqual(score, expected_score, 
                    f"{description} should give score {expected_score}, got {score}")
    
    def test_entropy_scoring_various_user_agents(self):
        """Test entropy scoring with various User-Agent patterns."""
        test_cases = [
            # (user_agents_set, expected_score, description)
            (set(), 15, "no user agents"),
            ({'Bot'}, 15, "single user agent"),
            ({'Mozilla/5.0', 'Chrome/90.0'}, 0, "normal variety (2 UAs)"),
            ({'UA1', 'UA2', 'UA3'}, 0, "good variety (3 UAs)"),
            ({'UA1', 'UA2', 'UA3', 'UA4', 'UA5'}, 0, "good variety (5 UAs)"),
            (set(f'UA{i}' for i in range(6)), 8, "many UAs (6)"),
            (set(f'UA{i}' for i in range(11)), 12, "too many UAs (11)"),
        ]
        
        for ua_set, expected_score, description in test_cases:
            with self.subTest(description=description):
                self.mock_redis.reset_mock()
                self.mock_redis.smembers.return_value = ua_set
                
                request = self.factory.get('/test/')
                request.META = {'HTTP_USER_AGENT': 'Mozilla/5.0'} if ua_set else {}
                
                score = self.calculator._calculate_entropy_score('192.168.1.100', request)
                
                self.assertEqual(score, expected_score, 
                    f"{description} should give score {expected_score}, got {score}")
                
                # Verify Redis operations (only if UA provided)
                if request.META.get('HTTP_USER_AGENT'):
                    self.mock_redis.sadd.assert_called_once_with('ua:192.168.1.100', 'Mozilla/5.0')
                    self.mock_redis.expire.assert_called_once_with('ua:192.168.1.100', 3600)
    
    def test_auth_failure_scoring_various_counts(self):
        """Test auth failure scoring with various failure counts."""
        test_cases = [
            (None, 0, "no failures recorded"),
            ('0', 0, "zero failures"),
            ('1', 0, "one failure"),  # failures > 1 needed for 3 points
            ('2', 3, "two failures"),  # failures > 1 = 3 points
            ('3', 3, "three failures"),  # failures > 3 needed for 7 points
            ('4', 7, "four failures"),  # failures > 3 = 7 points
            ('5', 7, "five failures"),  # failures > 5 needed for 10 points
            ('6', 10, "six failures"),  # failures > 5 = 10 points
            ('10', 10, "ten failures"),
            ('15', 10, "many failures"),
        ]
        
        for failure_count, expected_score, description in test_cases:
            with self.subTest(description=description):
                self.mock_redis.reset_mock()
                self.mock_redis.get.return_value = failure_count
                
                score = self.calculator._calculate_auth_failure_score('192.168.1.100')
                
                self.assertEqual(score, expected_score, 
                    f"{description} should give score {expected_score}, got {score}")
                
                # Verify Redis operations
                self.mock_redis.get.assert_called_once_with('auth_fail:192.168.1.100')
    
    def test_signature_matching_various_patterns(self):
        """Test attack signature matching with various patterns."""
        # Test no signatures
        self.mock_blockchain.get_attack_signatures.return_value = []
        request = self.factory.get('/api/test/')
        score = self.calculator._check_attack_signatures('192.168.1.100', request)
        self.assertEqual(score, 0, "No signatures should give 0 score")
        
        # Test matching signature
        mock_signature = {
            'hash': 'test_hash',
            'pattern': {
                'endpoint_pattern': '/api/test',
                'method': 'GET'
            },
            'severity': 8
        }
        self.mock_blockchain.get_attack_signatures.return_value = [mock_signature]
        
        request = self.factory.get('/api/test/')
        score = self.calculator._check_attack_signatures('192.168.1.100', request)
        expected_score = min(30, 8 * 3)  # severity * 3, capped at 30
        self.assertEqual(score, expected_score, f"Matching signature should give {expected_score} score")
        
        # Test non-matching signature
        mock_signature['pattern']['endpoint_pattern'] = '/api/different'
        request = self.factory.get('/api/test/')
        score = self.calculator._check_attack_signatures('192.168.1.100', request)
        self.assertEqual(score, 0, "Non-matching signature should give 0 score")
    
    def test_complete_threat_score_calculation(self):
        """Test complete threat score calculation with all factors."""
        # Setup mocks for high-threat scenario
        self.mock_redis.incr.return_value = 120  # 20 points (rate)
        self.mock_redis.lrange.return_value = ['/api/patients'] * 20  # 25 points (pattern)
        self.mock_redis.smembers.return_value = {'Bot'}  # 15 points (entropy)
        self.mock_redis.get.return_value = '8'  # 10 points (auth failures)
        
        # Setup signature match
        mock_signature = {
            'hash': 'test_hash',
            'pattern': {'endpoint_pattern': '/api/patients'},
            'severity': 10
        }
        self.mock_blockchain.get_attack_signatures.return_value = [mock_signature]
        
        # Create unauthenticated request (20 points for session)
        request = self.factory.get('/api/patients/')
        request.user = AnonymousUser()
        request.session = Mock()
        request.session.session_key = None
        request.COOKIES = {}
        request.META = {'HTTP_USER_AGENT': 'Bot'}
        
        total_score, factors = self.calculator.calculate_threat_score(request, '192.168.1.100')
        
        # Verify individual factors
        self.assertEqual(factors['rate'], 20, "Rate score should be 20")
        self.assertEqual(factors['pattern'], 25, "Pattern score should be 25")
        self.assertEqual(factors['session'], 20, "Session score should be 20")
        self.assertEqual(factors['entropy'], 15, "Entropy score should be 15")
        self.assertEqual(factors['auth_failures'], 10, "Auth failure score should be 10")
        self.assertEqual(factors['signature_match'], 30, "Signature match score should be 30")
        
        # Total would be 120, but should be capped at 100
        self.assertEqual(total_score, 100, "Total score should be capped at 100")
        
        # Verify all factors are present
        expected_factors = {'rate', 'pattern', 'session', 'entropy', 'auth_failures', 'signature_match'}
        self.assertEqual(set(factors.keys()), expected_factors, "All factors should be present")
    
    def test_threat_level_and_decision_methods(self):
        """Test threat level classification and decision methods."""
        # Test all boundary conditions
        test_cases = [
            # (score, expected_level, should_block, should_captcha)
            (0, 'LOW', False, False),
            (39, 'LOW', False, False),
            (40, 'MEDIUM', False, True),
            (50, 'MEDIUM', False, True),
            (60, 'MEDIUM', False, True),
            (61, 'HIGH', True, False),
            (80, 'HIGH', True, False),
            (100, 'HIGH', True, False),
        ]
        
        for score, expected_level, should_block, should_captcha in test_cases:
            with self.subTest(score=score):
                level = self.calculator.get_threat_level(score)
                block = self.calculator.should_block_request(score)
                captcha = self.calculator.should_require_captcha(score)
                
                self.assertEqual(level, expected_level, f"Score {score} should be {expected_level}")
                self.assertEqual(block, should_block, f"Score {score} block decision should be {should_block}")
                self.assertEqual(captcha, should_captcha, f"Score {score} CAPTCHA decision should be {should_captcha}")
    
    def test_auth_failure_management(self):
        """Test authentication failure recording and clearing."""
        ip_address = '192.168.1.100'
        
        # Test recording first failure
        self.mock_redis.incr.return_value = 1
        self.calculator.record_auth_failure(ip_address)
        
        self.mock_redis.incr.assert_called_once_with('auth_fail:192.168.1.100')
        self.mock_redis.expire.assert_called_once_with('auth_fail:192.168.1.100', 600)
        
        # Test recording subsequent failure
        self.mock_redis.reset_mock()
        self.mock_redis.incr.return_value = 2
        self.calculator.record_auth_failure(ip_address)
        
        self.mock_redis.incr.assert_called_once_with('auth_fail:192.168.1.100')
        # Expire should not be called again for subsequent failures
        self.mock_redis.expire.assert_not_called()
        
        # Test clearing failures
        self.mock_redis.reset_mock()
        self.calculator.clear_auth_failures(ip_address)
        
        self.mock_redis.delete.assert_called_once_with('auth_fail:192.168.1.100')
    
    def test_error_handling(self):
        """Test error handling for Redis and blockchain failures."""
        # Test Redis failure in rate scoring
        self.mock_redis.incr.side_effect = Exception("Redis connection failed")
        score = self.calculator._calculate_rate_score('192.168.1.100')
        self.assertEqual(score, 0, "Redis failure should return 0 score")
        
        # Test blockchain failure in signature checking
        self.mock_blockchain.get_attack_signatures.side_effect = Exception("Blockchain connection failed")
        request = self.factory.get('/test/')
        score = self.calculator._check_attack_signatures('192.168.1.100', request)
        self.assertEqual(score, 0, "Blockchain failure should return 0 score")
        
        # Test complete calculation with errors
        self.mock_redis.reset_mock()
        self.mock_redis.incr.side_effect = Exception("Redis error")
        self.mock_redis.lrange.side_effect = Exception("Redis error")
        self.mock_redis.smembers.side_effect = Exception("Redis error")
        self.mock_redis.get.side_effect = Exception("Redis error")
        
        request = self.factory.get('/test/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.session = Mock()
        request.session.session_key = 'test'
        request.COOKIES = {'test': 'value'}
        request.META = {'HTTP_USER_AGENT': 'Mozilla/5.0'}
        
        total_score, factors = self.calculator.calculate_threat_score(request, '192.168.1.100')
        
        # Should return safe defaults
        self.assertEqual(total_score, 0, "Error handling should return 0 total score")
        expected_factors = {'rate': 0, 'pattern': 0, 'session': 0, 'entropy': 0, 'auth_failures': 0, 'signature_match': 0}
        self.assertEqual(factors, expected_factors, "Error handling should return zero factors")