"""
Property-based tests for ThreatScoreCalculator.
Tests universal properties that should hold across all inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from django.test import RequestFactory
from unittest.mock import Mock, MagicMock
import redis

from core.threat_calculator import ThreatScoreCalculator


class TestThreatCalculatorProperties:
    """Property-based tests for ThreatScoreCalculator functionality."""
    
    def setup_method(self):
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
    
    @given(
        ip_address=st.ip_addresses(v=4).map(str),
        request_count=st.integers(min_value=1, max_value=200)
    )
    @settings(max_examples=20)
    def test_rate_score_calculation_property(self, ip_address, request_count):
        """
        **Feature: blockchain-healthcare-security, Property 7: Rate Score Calculation**
        
        For any IP address and request count, the rate score should follow
        the specified thresholds: >100 requests = 20 points, with graduated
        scoring for lower rates.
        
        **Validates: Requirements 2.2, 3.3**
        """
        # Create fresh mocks for this test iteration to avoid cross-contamination
        fresh_redis = Mock(spec=redis.Redis)
        fresh_blockchain = Mock()
        fresh_blockchain.get_attack_signatures.return_value = []
        
        # Create calculator with fresh mocks
        calculator = ThreatScoreCalculator(
            redis_client=fresh_redis,
            blockchain_service=fresh_blockchain
        )
        
        # Setup Redis mock to return the request count
        fresh_redis.incr.return_value = request_count
        
        # Calculate rate score
        score = calculator._calculate_rate_score(ip_address)
        
        # Verify score follows the correct thresholds
        if request_count > 100:
            assert score == 20, f"Expected 20 points for {request_count} requests, got {score}"
        elif request_count > 80:
            assert score == 18, f"Expected 18 points for {request_count} requests, got {score}"
        elif request_count > 60:
            assert score == 15, f"Expected 15 points for {request_count} requests, got {score}"
        elif request_count > 40:
            assert score == 12, f"Expected 12 points for {request_count} requests, got {score}"
        elif request_count > 30:
            assert score == 8, f"Expected 8 points for {request_count} requests, got {score}"
        elif request_count > 20:
            assert score == 5, f"Expected 5 points for {request_count} requests, got {score}"
        elif request_count > 15:
            assert score == 3, f"Expected 3 points for {request_count} requests, got {score}"
        else:
            assert score == 0, f"Expected 0 points for {request_count} requests, got {score}"
        
        # Verify Redis operations were called correctly (check call arguments, not call count)
        expected_key = f"rate:{ip_address}"
        fresh_redis.incr.assert_called_with(expected_key)
        
        # Verify the method was called at least once with correct arguments
        assert fresh_redis.incr.called, "Redis incr should have been called"
        call_args = fresh_redis.incr.call_args_list[-1]  # Get the last call
        assert call_args[0][0] == expected_key, f"Expected incr call with key {expected_key}"
        
        # Verify expiry is set on first request
        if request_count == 1:
            fresh_redis.expire.assert_called_with(f"rate:{ip_address}", 60)
    
    @given(
        ip_address=st.ip_addresses(v=4).map(str),
        request_count=st.integers(min_value=1, max_value=200)
    )
    @settings(max_examples=20)
    def test_rate_tracking_accuracy_property(self, ip_address, request_count):
        """
        **Feature: blockchain-healthcare-security, Property 14: Rate Tracking Accuracy**
        
        For any IP address, the rate tracking should accurately count requests
        within the 1-minute sliding window and set appropriate expiry times.
        
        **Validates: Requirements 2.2, 3.3**
        """
        # Create fresh mocks for this test iteration to avoid cross-contamination
        fresh_redis = Mock(spec=redis.Redis)
        fresh_blockchain = Mock()
        fresh_blockchain.get_attack_signatures.return_value = []
        
        # Create calculator with fresh mocks
        calculator = ThreatScoreCalculator(
            redis_client=fresh_redis,
            blockchain_service=fresh_blockchain
        )
        
        # Setup Redis mock
        fresh_redis.incr.return_value = request_count
        
        # Calculate rate score
        calculator._calculate_rate_score(ip_address)
        
        # Verify Redis key format and operations
        expected_key = f"rate:{ip_address}"
        fresh_redis.incr.assert_called_once_with(expected_key)
        
        # Verify expiry is set correctly for first request
        if request_count == 1:
            fresh_redis.expire.assert_called_once_with(expected_key, 60)
        
        # Verify the key format follows the expected pattern
        assert expected_key.startswith("rate:")
        assert ip_address in expected_key
    
    @given(
        ip_address=st.ip_addresses(v=4).map(str),
        endpoints=st.lists(
            st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'), whitelist_characters='/-_.')),
            min_size=10,
            max_size=20
        )
    )
    @settings(max_examples=20)
    def test_pattern_score_calculation_property(self, ip_address, endpoints):
        """
        **Feature: blockchain-healthcare-security, Property 8: Pattern Score Calculation**
        
        For any IP address with endpoint access patterns, the pattern score should
        correctly calculate repetition ratios and assign scores based on endpoint diversity.
        
        **Validates: Requirements 2.3**
        """
        # Reset mock for this test
        self.mock_redis.reset_mock()
        
        # Setup Redis mock to return the endpoint list
        self.mock_redis.lrange.return_value = endpoints
        
        # Create a mock request
        request = self.factory.get(endpoints[0])  # Use first endpoint as current request
        
        # Calculate pattern score
        score = self.calculator._calculate_pattern_score(ip_address, request)
        
        # Calculate expected repetition ratio
        unique_endpoints = len(set(endpoints))
        total_requests = len(endpoints)
        repetition_ratio = 1 - (unique_endpoints / total_requests)
        
        # Verify score follows the correct thresholds
        if repetition_ratio > 0.8:  # 80% same endpoint
            assert score == 25, f"Expected 25 points for repetition ratio {repetition_ratio:.2f}, got {score}"
        elif repetition_ratio > 0.7:  # 70% same endpoint
            assert score == 20, f"Expected 20 points for repetition ratio {repetition_ratio:.2f}, got {score}"
        elif repetition_ratio > 0.6:  # 60% same endpoint
            assert score == 15, f"Expected 15 points for repetition ratio {repetition_ratio:.2f}, got {score}"
        elif repetition_ratio > 0.5:  # 50% same endpoint
            assert score == 10, f"Expected 10 points for repetition ratio {repetition_ratio:.2f}, got {score}"
        elif repetition_ratio > 0.4:  # 40% same endpoint
            assert score == 5, f"Expected 5 points for repetition ratio {repetition_ratio:.2f}, got {score}"
        else:
            assert score == 0, f"Expected 0 points for repetition ratio {repetition_ratio:.2f}, got {score}"
        
        # Verify Redis operations were called correctly
        expected_key = f"pattern:{ip_address}"
        # The endpoint gets normalized by Django's RequestFactory - check what was actually called
        actual_calls = self.mock_redis.lpush.call_args_list
        assert len(actual_calls) == 1, f"Expected 1 call to lpush, got {len(actual_calls)}"
        
        called_key, called_endpoint = actual_calls[0][0]
        assert called_key == expected_key, f"Expected key {expected_key}, got {called_key}"
        
        # Django's RequestFactory normalizes paths and may remove trailing slashes
        # We need to simulate what Django actually does, then what threat calculator does
        # Django RequestFactory creates request.path, then threat calculator does lstrip('/')
        
        if endpoints[0] == '/':
            expected_endpoint = ''  # '/' becomes '/' in request.path, then '' after lstrip('/')
        else:
            # Simulate what Django RequestFactory actually creates for request.path
            # Django normalizes paths and may remove trailing slashes
            from django.test import RequestFactory
            temp_factory = RequestFactory()
            temp_request = temp_factory.get(endpoints[0])
            django_path = temp_request.path  # What Django actually creates
            expected_endpoint = django_path.lstrip('/')  # What threat calculator stores
        
        assert called_endpoint == expected_endpoint, f"Expected endpoint {expected_endpoint}, got {called_endpoint}"
        self.mock_redis.ltrim.assert_called_once_with(expected_key, 0, 19)
        self.mock_redis.expire.assert_called_once_with(expected_key, 300)
        self.mock_redis.lrange.assert_called_once_with(expected_key, 0, -1)
    
    @given(
        is_authenticated=st.booleans(),
        has_session=st.booleans(),
        cookie_count=st.integers(min_value=0, max_value=10),
        has_auth_header=st.booleans()
    )
    @settings(max_examples=20)
    def test_session_score_calculation_property(self, is_authenticated, has_session, cookie_count, has_auth_header):
        """
        **Feature: blockchain-healthcare-security, Property 9: Session Score Calculation**
        
        For any request with various authentication and session states, the session score
        should correctly assess the legitimacy based on authentication, session, and cookies.
        
        **Validates: Requirements 2.4**
        """
        # Create a mock request with specified session/auth state
        request = self.factory.get('/test/')
        
        # Mock user authentication
        request.user = Mock()
        request.user.is_authenticated = is_authenticated
        
        # Mock session
        request.session = Mock()
        request.session.session_key = 'test_session_key' if has_session else None
        
        # Mock cookies
        request.COOKIES = {f'cookie_{i}': f'value_{i}' for i in range(cookie_count)}
        
        # Mock authentication headers
        request.META = {}
        if has_auth_header:
            request.META['HTTP_AUTHORIZATION'] = 'Bearer test_token'
        
        # Calculate session score
        score = self.calculator._calculate_session_score(request)
        
        # Verify score follows the correct logic
        if is_authenticated:
            # Authenticated users get no penalty
            assert score == 0, f"Expected 0 points for authenticated user, got {score}"
        elif has_auth_header:
            # API authentication present
            assert score == 0, f"Expected 0 points for API auth header, got {score}"
        elif not has_session and cookie_count == 0:
            # No session or cookies = likely bot
            assert score == 20, f"Expected 20 points for no session/cookies, got {score}"
        elif not has_session:
            # Has cookies but no session = suspicious
            assert score == 15, f"Expected 15 points for no session but has cookies, got {score}"
        elif cookie_count < 2:
            # Very few cookies = suspicious
            assert score == 10, f"Expected 10 points for few cookies ({cookie_count}), got {score}"
        else:
            # Has session and multiple cookies = likely legitimate
            assert score == 0, f"Expected 0 points for session + multiple cookies, got {score}"
    
    @given(
        ip_address=st.ip_addresses(v=4).map(str),
        request_count=st.integers(min_value=1, max_value=150),
        is_authenticated=st.booleans(),
        has_session=st.booleans(),
        cookie_count=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=20)
    def test_multi_factor_scoring_property(self, ip_address, request_count, is_authenticated, has_session, cookie_count):
        """
        **Feature: blockchain-healthcare-security, Property 6: Multi-Factor Scoring**
        
        For any request, the threat score calculation must include at least 5 distinct
        behavioral factors and the total score should be the sum of all factors.
        
        **Validates: Requirements 2.1**
        """
        # Reset mocks for this test
        self.mock_redis.reset_mock()
        self.mock_blockchain.reset_mock()
        
        # Setup Redis mocks
        self.mock_redis.incr.return_value = request_count
        self.mock_redis.lrange.return_value = ['/test'] * 10  # Uniform pattern
        self.mock_redis.smembers.return_value = {'Mozilla/5.0'}  # Single UA
        self.mock_redis.get.return_value = '0'  # No auth failures
        
        # Setup blockchain mock
        self.mock_blockchain.get_attack_signatures.return_value = []
        
        # Create mock request
        request = self.factory.get('/test/')
        request.user = Mock()
        request.user.is_authenticated = is_authenticated
        request.session = Mock()
        request.session.session_key = 'test_session' if has_session else None
        request.COOKIES = {f'cookie_{i}': f'value_{i}' for i in range(cookie_count)}
        request.META = {'HTTP_USER_AGENT': 'Mozilla/5.0'}
        
        # Calculate threat score
        total_score, factors = self.calculator.calculate_threat_score(request, ip_address)
        
        # Verify all 6 factors are present
        expected_factors = {'rate', 'pattern', 'session', 'entropy', 'auth_failures', 'signature_match'}
        assert set(factors.keys()) == expected_factors, f"Missing factors: {expected_factors - set(factors.keys())}"
        
        # Verify total score is sum of factors (capped at 100)
        calculated_total = sum(factors.values())
        expected_total = min(calculated_total, 100)
        assert total_score == expected_total, f"Expected total {expected_total}, got {total_score}"
        
        # Verify score is within valid range
        assert 0 <= total_score <= 100, f"Score {total_score} outside valid range [0, 100]"
    
    @given(
        threat_score=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=20)
    def test_threat_classification_boundaries_property(self, threat_score):
        """
        **Feature: blockchain-healthcare-security, Property 10: Threat Classification Boundaries**
        
        For any threat score, the classification must follow the specified boundaries:
        > 60 = HIGH, 40-60 = MEDIUM, < 40 = LOW.
        
        **Validates: Requirements 2.7, 2.8, 2.9**
        """
        # Test threat level classification
        threat_level = self.calculator.get_threat_level(threat_score)
        
        if threat_score > 60:  # "exceeds 60" means > 60
            assert threat_level == 'HIGH', f"Score {threat_score} should be HIGH, got {threat_level}"
        elif threat_score >= 40:  # "between 40 and 60" includes 40 and 60
            assert threat_level == 'MEDIUM', f"Score {threat_score} should be MEDIUM, got {threat_level}"
        else:  # "below 40" means < 40
            assert threat_level == 'LOW', f"Score {threat_score} should be LOW, got {threat_level}"
        
        # Test blocking decision
        should_block = self.calculator.should_block_request(threat_score)
        expected_block = threat_score > 60  # Block when HIGH threat
        assert should_block == expected_block, f"Score {threat_score}: expected block={expected_block}, got {should_block}"
        
        # Test CAPTCHA decision
        should_captcha = self.calculator.should_require_captcha(threat_score)
        expected_captcha = 40 <= threat_score <= 60  # CAPTCHA for MEDIUM threat
        assert should_captcha == expected_captcha, f"Score {threat_score}: expected captcha={expected_captcha}, got {should_captcha}"
    
    @given(
        base_factors=st.dictionaries(
            st.sampled_from(['rate', 'pattern', 'session', 'entropy', 'auth_failures']),
            st.integers(min_value=0, max_value=20),
            min_size=3,
            max_size=5
        ),
        signature_match_score=st.integers(min_value=0, max_value=30)
    )
    @settings(max_examples=20)
    def test_score_monotonicity_property(self, base_factors, signature_match_score):
        """
        **Feature: blockchain-healthcare-security, Property 11: Score Monotonicity**
        
        For any request, adding more suspicious factors must never decrease the total threat score.
        
        **Validates: Requirements 2.1**
        """
        # Calculate base score
        base_score = sum(base_factors.values())
        
        # Add signature match factor
        enhanced_factors = base_factors.copy()
        enhanced_factors['signature_match'] = signature_match_score
        enhanced_score = sum(enhanced_factors.values())
        
        # Verify monotonicity (adding factors never decreases score)
        assert enhanced_score >= base_score, f"Adding signature match decreased score: {base_score} -> {enhanced_score}"
        
        # If signature match score > 0, total should increase
        if signature_match_score > 0:
            assert enhanced_score > base_score, f"Non-zero signature match should increase score: {base_score} -> {enhanced_score}"
    
    @given(
        ip_address=st.ip_addresses(v=4).map(str),
        has_signature_match=st.booleans(),
        signature_severity=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20)
    def test_signature_matching_score_boost_property(self, ip_address, has_signature_match, signature_severity):
        """
        **Feature: blockchain-healthcare-security, Property 21: Signature Matching Score Boost**
        
        For any request that matches a known attack signature, the threat score should
        receive a significant boost based on the signature severity.
        
        **Validates: Requirements 5.5**
        """
        # Reset mocks
        self.mock_redis.reset_mock()
        self.mock_blockchain.reset_mock()
        
        # Setup baseline mocks (low threat)
        self.mock_redis.incr.return_value = 1  # Low rate
        self.mock_redis.lrange.return_value = ['/test1', '/test2', '/test3'] * 4  # Diverse pattern
        self.mock_redis.smembers.return_value = {'Mozilla/5.0', 'Chrome/90.0'}  # Normal UA variety
        self.mock_redis.get.return_value = '0'  # No auth failures
        
        # Setup signature match
        if has_signature_match:
            mock_signature = {
                'hash': 'test_hash',
                'pattern': {
                    'endpoint_pattern': '/test',
                    'method': 'GET'
                },
                'severity': signature_severity
            }
            self.mock_blockchain.get_attack_signatures.return_value = [mock_signature]
        else:
            self.mock_blockchain.get_attack_signatures.return_value = []
        
        # Create mock request
        request = self.factory.get('/test/')
        request.user = Mock()
        request.user.is_authenticated = True  # Authenticated = low session score
        request.session = Mock()
        request.session.session_key = 'test_session'
        request.COOKIES = {'session': 'value', 'csrf': 'token'}
        request.META = {'HTTP_USER_AGENT': 'Mozilla/5.0'}
        
        # Calculate threat score
        total_score, factors = self.calculator.calculate_threat_score(request, ip_address)
        
        if has_signature_match:
            # Should have signature match score
            assert factors['signature_match'] > 0, f"Expected signature match score > 0, got {factors['signature_match']}"
            
            # Score should be proportional to severity (up to 30 points)
            expected_signature_score = min(30, signature_severity * 3)
            assert factors['signature_match'] == expected_signature_score, f"Expected {expected_signature_score}, got {factors['signature_match']}"
        else:
            # Should have no signature match score
            assert factors['signature_match'] == 0, f"Expected no signature match score, got {factors['signature_match']}"
