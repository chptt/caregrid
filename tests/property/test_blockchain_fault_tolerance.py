"""
Property-based tests for BlockchainService fault tolerance and caching

These tests validate universal properties that must hold for blockchain service
fault tolerance and caching behavior, using Hypothesis to generate random test cases.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck
from unittest.mock import Mock, patch, MagicMock
from web3 import Web3
from web3.exceptions import ProviderConnectionError, TimeExhausted
import json
import time
import redis
from datetime import datetime, timedelta


# Custom strategies for blockchain operations
@st.composite
def patient_id_hash_strategy(draw):
    """Generate valid patient ID hashes (32 bytes)"""
    return draw(st.binary(min_size=32, max_size=32))


@st.composite
def ip_hash_strategy(draw):
    """Generate valid IP hashes (32 bytes)"""
    return draw(st.binary(min_size=32, max_size=32))


@st.composite
def cache_key_strategy(draw):
    """Generate valid cache keys"""
    return draw(st.text(
        min_size=5,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_:-'
        )
    ))


class TestBlockchainCachingProperties:
    """
    Property-based tests for blockchain caching behavior.
    
    These tests validate:
    - Property 33: Blockchain Caching
    """
    
    @settings(max_examples=100)
    @given(
        patient_id_hash=patient_id_hash_strategy(),
        cache_ttl=st.integers(min_value=60, max_value=3600)  # 1 minute to 1 hour
    )
    def test_property_33_blockchain_caching(self, patient_id_hash, cache_ttl):
        """
        Feature: blockchain-healthcare-security, Property 33: Blockchain Caching
        
        For any blockchain read operation performed twice within the cache TTL,
        the second read must use cached data without making an RPC call.
        
        Validates: Requirements 9.4
        """
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.get.return_value = None  # Initially no cache
        mock_redis.setex.return_value = True
        
        # Mock Web3 and contract
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = True
        mock_contract = Mock()
        
        # Set up the blockchain service with mocked dependencies
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract), \
             patch('core.blockchain_service.settings') as mock_settings:
            
            # Mock Django settings
            mock_settings.BLOCKCHAIN_PROVIDER_URL = 'http://localhost:8545'
            mock_settings.REDIS_HOST = 'localhost'
            mock_settings.REDIS_PORT = 6379
            mock_settings.REDIS_DB = 0
            mock_settings.BLOCKCHAIN_GAS_LIMIT = 500000
            mock_settings.BLOCKCHAIN_CONFIRMATION_TIMEOUT = 30
            
            service = BlockchainService()
            service.cache_timeout = cache_ttl
            
            # Convert patient_id_hash to hex string for the test
            patient_id_hex = "0x" + patient_id_hash.hex()
            
            # Mock the blockchain call to return a specific result
            expected_result = True
            mock_contract.functions.isPatientRegistered.return_value.call.return_value = expected_result
            
            # First call - should hit blockchain and cache the result
            mock_redis.get.return_value = None  # No cache initially
            result1 = service.is_patient_registered(patient_id_hex)
            
            # Verify blockchain was called
            mock_contract.functions.isPatientRegistered.assert_called_once()
            
            # Verify result was cached
            cache_key = f"patient_registered:{patient_id_hex}"
            mock_redis.setex.assert_called_with(cache_key, cache_ttl, json.dumps(expected_result, default=str))
            
            # Reset mocks for second call
            mock_contract.functions.isPatientRegistered.reset_mock()
            
            # Second call within TTL - should use cache, not hit blockchain
            mock_redis.get.return_value = json.dumps(expected_result)  # Cache hit
            result2 = service.is_patient_registered(patient_id_hex)
            
            # Verify blockchain was NOT called again (cached result used)
            mock_contract.functions.isPatientRegistered.assert_not_called()
            
            # Verify both results are identical
            assert result1 == result2 == expected_result, (
                f"For any blockchain read operation performed twice within the cache TTL, "
                f"both results must be identical. Got result1={result1}, result2={result2}"
            )
            
            # Verify the second call used cached data (no additional blockchain RPC)
            # This is validated by ensuring the contract method was not called again
    
    @settings(max_examples=50)
    @given(
        ip_hash=ip_hash_strategy(),
        cache_ttl=st.integers(min_value=60, max_value=3600)
    )
    def test_property_33_ip_blocking_cache(self, ip_hash, cache_ttl):
        """
        Feature: blockchain-healthcare-security, Property 33: Blockchain Caching (IP Blocking)
        
        For any IP blocking check performed twice within the cache TTL,
        the second check must use cached data without making an RPC call.
        
        Validates: Requirements 9.4
        """
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.get.return_value = None  # Initially no cache
        mock_redis.setex.return_value = True
        
        # Mock Web3 and contract
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = True
        mock_contract = Mock()
        
        # Set up the blockchain service with mocked dependencies
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            service.cache_timeout = cache_ttl
            
            # Convert ip_hash to hex string for the test
            ip_hash_hex = "0x" + ip_hash.hex()
            
            # Mock the blockchain call to return a specific result
            expected_result = True  # IP is blocked
            mock_contract.functions.isIPBlocked.return_value.call.return_value = expected_result
            
            # First call - should hit blockchain and cache the result
            mock_redis.get.return_value = None  # No cache initially
            result1 = service.is_ip_blocked(ip_hash_hex)
            
            # Verify blockchain was called
            mock_contract.functions.isIPBlocked.assert_called_once()
            
            # Verify result was cached with shorter TTL for IP blocks (60 seconds)
            cache_key = f"ip_blocked:{ip_hash_hex}"
            mock_redis.setex.assert_called_with(cache_key, 60, json.dumps(expected_result, default=str))
            
            # Reset mocks for second call
            mock_contract.functions.isIPBlocked.reset_mock()
            
            # Second call within TTL - should use cache, not hit blockchain
            mock_redis.get.return_value = json.dumps(expected_result)  # Cache hit
            result2 = service.is_ip_blocked(ip_hash_hex)
            
            # Verify blockchain was NOT called again (cached result used)
            mock_contract.functions.isIPBlocked.assert_not_called()
            
            # Verify both results are identical
            assert result1 == result2 == expected_result, (
                f"For any IP blocking check performed twice within the cache TTL, "
                f"both results must be identical. Got result1={result1}, result2={result2}"
            )
    
    @settings(max_examples=50)
    @given(
        cache_key=cache_key_strategy(),
        cached_value=st.one_of(
            st.booleans(),
            st.integers(),
            st.text(min_size=1, max_size=100),
            st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), min_size=1, max_size=5)
        )
    )
    def test_property_33_cache_consistency(self, cache_key, cached_value):
        """
        Feature: blockchain-healthcare-security, Property 33: Blockchain Caching (Cache Consistency)
        
        For any cached value, retrieving it multiple times must return the same result
        until the cache expires.
        
        Validates: Requirements 9.4
        """
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client
        mock_redis = Mock()
        
        # Set up the blockchain service with mocked dependencies
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3'), \
             patch.object(BlockchainService, '_load_contract'):
            
            service = BlockchainService()
            
            # Test cache set and get operations
            service._cache_set(cache_key, cached_value)
            
            # Verify cache was set with correct parameters
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == cache_key  # Key
            assert call_args[0][1] == service.cache_timeout  # TTL
            assert call_args[0][2] == json.dumps(cached_value, default=str)  # Serialized value
            
            # Mock cache retrieval
            mock_redis.get.return_value = json.dumps(cached_value, default=str)
            
            # Multiple cache retrievals should return the same value
            result1 = service._cache_get(cache_key)
            result2 = service._cache_get(cache_key)
            result3 = service._cache_get(cache_key)
            
            # All results should be identical to the original cached value
            assert result1 == cached_value, f"First cache retrieval should match original value"
            assert result2 == cached_value, f"Second cache retrieval should match original value"
            assert result3 == cached_value, f"Third cache retrieval should match original value"
            assert result1 == result2 == result3, f"All cache retrievals should be identical"


class TestBlockchainFaultToleranceProperties:
    """
    Property-based tests for blockchain fault tolerance behavior.
    
    These tests validate:
    - Property 34: Fault Tolerance
    """
    
    @settings(max_examples=50)
    @given(
        patient_id_hash=patient_id_hash_strategy(),
        cached_result=st.booleans()
    )
    def test_property_34_fault_tolerance_patient_check(self, patient_id_hash, cached_result):
        """
        Feature: blockchain-healthcare-security, Property 34: Fault Tolerance (Patient Check)
        
        For any blockchain connection failure during patient registration check,
        the system must continue operating using cached data and must not crash.
        
        Validates: Requirements 9.5
        """
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client with cached data
        mock_redis = Mock()
        mock_redis.get.return_value = json.dumps(cached_result)  # Cache available
        
        # Mock Web3 to simulate connection failure
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = False  # Connection failed
        
        # Mock contract that will raise connection error
        mock_contract = Mock()
        mock_contract.functions.isPatientRegistered.return_value.call.side_effect = ProviderConnectionError("Connection failed")
        
        # Set up the blockchain service with mocked dependencies
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            
            # Convert patient_id_hash to hex string for the test
            patient_id_hex = "0x" + patient_id_hash.hex()
            
            # Call should not crash despite blockchain connection failure
            try:
                result = service.is_patient_registered(patient_id_hex)
                
                # Should return cached result, not crash
                assert result == cached_result, (
                    f"For any blockchain connection failure, the system must return cached data. "
                    f"Expected {cached_result}, got {result}"
                )
                
                # Verify cache was accessed
                cache_key = f"patient_registered:{patient_id_hex}"
                mock_redis.get.assert_called_with(cache_key)
                
            except Exception as e:
                pytest.fail(
                    f"For any blockchain connection failure, the system must not crash. "
                    f"Got exception: {type(e).__name__}: {e}"
                )
    
    @settings(max_examples=50)
    @given(
        ip_hash=ip_hash_strategy(),
        cached_result=st.booleans()
    )
    def test_property_34_fault_tolerance_ip_check(self, ip_hash, cached_result):
        """
        Feature: blockchain-healthcare-security, Property 34: Fault Tolerance (IP Check)
        
        For any blockchain connection failure during IP blocking check,
        the system must continue operating using cached data and must not crash.
        
        Validates: Requirements 9.5
        """
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client with cached data
        mock_redis = Mock()
        mock_redis.get.return_value = json.dumps(cached_result)  # Cache available
        
        # Mock Web3 to simulate connection failure
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = False  # Connection failed
        
        # Mock contract that will raise connection error
        mock_contract = Mock()
        mock_contract.functions.isIPBlocked.return_value.call.side_effect = ProviderConnectionError("Connection failed")
        
        # Set up the blockchain service with mocked dependencies
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            
            # Convert ip_hash to hex string for the test
            ip_hash_hex = "0x" + ip_hash.hex()
            
            # Call should not crash despite blockchain connection failure
            try:
                result = service.is_ip_blocked(ip_hash_hex)
                
                # Should return cached result, not crash
                assert result == cached_result, (
                    f"For any blockchain connection failure, the system must return cached data. "
                    f"Expected {cached_result}, got {result}"
                )
                
                # Verify cache was accessed
                cache_key = f"ip_blocked:{ip_hash_hex}"
                mock_redis.get.assert_called_with(cache_key)
                
            except Exception as e:
                pytest.fail(
                    f"For any blockchain connection failure, the system must not crash. "
                    f"Got exception: {type(e).__name__}: {e}"
                )
    
    @settings(max_examples=30)
    @given(
        operation_type=st.sampled_from(['patient_check', 'ip_check', 'attack_signatures']),
        failure_type=st.sampled_from([
            ProviderConnectionError("Network unreachable"),
            TimeExhausted("Transaction timeout"),
            ConnectionError("Connection refused"),
            Exception("Generic blockchain error")
        ])
    )
    def test_property_34_fault_tolerance_no_cache(self, operation_type, failure_type):
        """
        Feature: blockchain-healthcare-security, Property 34: Fault Tolerance (No Cache Available)
        
        For any blockchain connection failure when no cached data is available,
        the system must return a safe default value and must not crash.
        
        Validates: Requirements 9.5
        """
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client with no cached data
        mock_redis = Mock()
        mock_redis.get.return_value = None  # No cache available
        
        # Mock Web3 to simulate connection failure
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = False  # Connection failed
        
        # Mock contract that will raise the specified failure
        mock_contract = Mock()
        
        # Set up the blockchain service with mocked dependencies
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            
            # Test different operation types
            test_hash = "0x" + ("a" * 64)  # Valid hex hash
            
            try:
                if operation_type == 'patient_check':
                    mock_contract.functions.isPatientRegistered.return_value.call.side_effect = failure_type
                    result = service.is_patient_registered(test_hash)
                    # Should return False (safe default) when no cache and blockchain fails
                    assert result is False, (
                        f"Patient check should return False (safe default) when blockchain fails and no cache available"
                    )
                    
                elif operation_type == 'ip_check':
                    mock_contract.functions.isIPBlocked.return_value.call.side_effect = failure_type
                    result = service.is_ip_blocked(test_hash)
                    # Should return False (safe default) when no cache and blockchain fails
                    assert result is False, (
                        f"IP check should return False (safe default) when blockchain fails and no cache available"
                    )
                    
                elif operation_type == 'attack_signatures':
                    mock_contract.functions.getAllSignatures.return_value.call.side_effect = failure_type
                    result = service.get_attack_signatures()
                    # Should return empty list (safe default) when no cache and blockchain fails
                    assert result == [], (
                        f"Attack signatures should return empty list (safe default) when blockchain fails and no cache available"
                    )
                
            except Exception as e:
                pytest.fail(
                    f"For any blockchain connection failure, the system must not crash even without cache. "
                    f"Operation: {operation_type}, Failure: {type(failure_type).__name__}, "
                    f"Got exception: {type(e).__name__}: {e}"
                )
    
    @settings(max_examples=30)
    @given(
        reconnect_success=st.booleans(),
        retry_count=st.integers(min_value=1, max_value=5)
    )
    def test_property_34_fault_tolerance_reconnection(self, reconnect_success, retry_count):
        """
        Feature: blockchain-healthcare-security, Property 34: Fault Tolerance (Reconnection)
        
        For any blockchain connection failure, the system must attempt to reconnect
        and continue operating gracefully regardless of reconnection success.
        
        Validates: Requirements 9.5
        """
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.get.return_value = None  # No cache
        
        # Mock Web3 connection behavior
        mock_w3 = Mock()
        mock_w3.is_connected.side_effect = [False] * retry_count + [reconnect_success]
        
        # Mock contract
        mock_contract = Mock()
        
        # Set up the blockchain service with mocked dependencies
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            
            # Test reconnection behavior
            try:
                # Initial connection check should fail
                initial_status = service.is_connected()
                assert initial_status is False, "Initial connection should fail"
                
                # Attempt reconnection
                reconnect_result = service.reconnect()
                
                if reconnect_success:
                    assert reconnect_result is True, "Reconnection should succeed when mocked to succeed"
                else:
                    assert reconnect_result is False, "Reconnection should fail when mocked to fail"
                
                # System should not crash regardless of reconnection outcome
                health_status = service.health_check()
                assert isinstance(health_status, dict), "Health check should return a dictionary"
                assert 'overall_status' in health_status, "Health check should include overall status"
                
                # Overall status should reflect the connection state appropriately
                if reconnect_success:
                    # If reconnection succeeded, status might be healthy or degraded
                    assert health_status['overall_status'] in ['healthy', 'degraded'], (
                        "Status should be healthy or degraded after successful reconnection"
                    )
                else:
                    # If reconnection failed, status should be degraded or unhealthy
                    assert health_status['overall_status'] in ['degraded', 'unhealthy'], (
                        "Status should be degraded or unhealthy after failed reconnection"
                    )
                
            except Exception as e:
                pytest.fail(
                    f"For any blockchain connection failure, reconnection attempts must not crash the system. "
                    f"Reconnect success: {reconnect_success}, Retry count: {retry_count}, "
                    f"Got exception: {type(e).__name__}: {e}"
                )
    
    @settings(max_examples=20)
    @given(
        redis_failure=st.booleans(),
        blockchain_failure=st.booleans()
    )
    def test_property_34_fault_tolerance_dual_failure(self, redis_failure, blockchain_failure):
        """
        Feature: blockchain-healthcare-security, Property 34: Fault Tolerance (Dual Failure)
        
        For any combination of Redis and blockchain failures, the system must
        continue operating and must not crash.
        
        Validates: Requirements 9.5
        """
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client behavior based on failure flag
        mock_redis = Mock()
        if redis_failure:
            mock_redis.get.side_effect = redis.ConnectionError("Redis connection failed")
            mock_redis.setex.side_effect = redis.ConnectionError("Redis connection failed")
            mock_redis.ping.side_effect = redis.ConnectionError("Redis connection failed")
        else:
            mock_redis.get.return_value = None  # No cache but Redis works
            mock_redis.setex.return_value = True
            mock_redis.ping.return_value = True
        
        # Mock Web3 behavior based on failure flag
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = not blockchain_failure
        
        # Mock contract behavior
        mock_contract = Mock()
        if blockchain_failure:
            mock_contract.functions.isPatientRegistered.return_value.call.side_effect = ProviderConnectionError("Blockchain failed")
        else:
            mock_contract.functions.isPatientRegistered.return_value.call.return_value = True
        
        # Set up the blockchain service with mocked dependencies
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            try:
                service = BlockchainService()
                
                # Test basic operations should not crash
                test_hash = "0x" + ("b" * 64)
                
                # Patient registration check
                result = service.is_patient_registered(test_hash)
                assert isinstance(result, bool), "Patient check should return a boolean even with failures"
                
                # Health check should work
                health = service.health_check()
                assert isinstance(health, dict), "Health check should return a dictionary even with failures"
                assert 'overall_status' in health, "Health check should include overall status"
                
                # Determine expected status based on failure combination
                if redis_failure and blockchain_failure:
                    assert health['overall_status'] == 'unhealthy', (
                        "System should be unhealthy when both Redis and blockchain fail"
                    )
                elif redis_failure or blockchain_failure:
                    assert health['overall_status'] in ['degraded', 'unhealthy'], (
                        "System should be degraded or unhealthy when one component fails"
                    )
                else:
                    assert health['overall_status'] in ['healthy', 'degraded'], (
                        "System should be healthy or degraded when no failures occur"
                    )
                
            except Exception as e:
                pytest.fail(
                    f"For any combination of Redis and blockchain failures, the system must not crash. "
                    f"Redis failure: {redis_failure}, Blockchain failure: {blockchain_failure}, "
                    f"Got exception: {type(e).__name__}: {e}"
                )


class TestBlockchainServiceEdgeCases:
    """
    Additional edge case tests for blockchain service fault tolerance.
    These complement the property-based tests with specific scenarios.
    """
    
    def test_execute_with_fallback_functionality(self):
        """Test the execute_with_fallback method with various scenarios"""
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client
        mock_redis = Mock()
        
        # Mock Web3
        mock_w3 = Mock()
        
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract'):
            
            service = BlockchainService()
            
            # Test successful blockchain operation
            mock_w3.is_connected.return_value = True
            
            def successful_func():
                return "blockchain_result"
            
            result = service.execute_with_fallback(successful_func)
            assert result == "blockchain_result", "Should return blockchain result when connection is good"
            
            # Test blockchain failure with cache fallback
            mock_w3.is_connected.return_value = False
            mock_redis.get.return_value = json.dumps("cached_result")
            
            def failing_func():
                raise ProviderConnectionError("Connection failed")
            
            result = service.execute_with_fallback(failing_func, cache_key="test_key")
            assert result == "cached_result", "Should return cached result when blockchain fails"
            
            # Test blockchain failure with default fallback
            mock_redis.get.return_value = None  # No cache
            
            result = service.execute_with_fallback(failing_func, cache_key="test_key", default_value="default")
            assert result == "default", "Should return default value when both blockchain and cache fail"
    
    def test_cache_error_handling(self):
        """Test that cache errors don't crash the system"""
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client that fails
        mock_redis = Mock()
        mock_redis.get.side_effect = redis.ConnectionError("Redis failed")
        mock_redis.setex.side_effect = redis.ConnectionError("Redis failed")
        
        # Mock Web3
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = True
        mock_contract = Mock()
        mock_contract.functions.isPatientRegistered.return_value.call.return_value = True
        
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            
            # Cache operations should not crash even if Redis fails
            try:
                service._cache_set("test_key", "test_value")
                result = service._cache_get("test_key")
                assert result is None, "Should return None when cache fails"
                
                # Blockchain operations should still work even if caching fails
                test_hash = "0x" + ("c" * 64)
                result = service.is_patient_registered(test_hash)
                assert result is True, "Should still get blockchain result even if caching fails"
                
            except Exception as e:
                pytest.fail(f"Cache errors should not crash the system: {type(e).__name__}: {e}")
    
    def test_clear_all_caches_with_redis_failure(self):
        """Test cache clearing when Redis fails"""
        from core.blockchain_service import BlockchainService
        
        # Mock Redis client that fails on some operations
        mock_redis = Mock()
        mock_redis.keys.side_effect = redis.ConnectionError("Redis failed")
        
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3'), \
             patch.object(BlockchainService, '_load_contract'):
            
            service = BlockchainService()
            
            # Should not crash when Redis fails during cache clearing
            try:
                result = service.clear_all_caches()
                assert result is False, "Should return False when cache clearing fails"
            except Exception as e:
                pytest.fail(f"Cache clearing should not crash when Redis fails: {type(e).__name__}: {e}")
    
    def test_health_check_comprehensive(self):
        """Test comprehensive health check under various failure conditions"""
        from core.blockchain_service import BlockchainService
        
        # Test all healthy
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = True
        mock_w3.eth.block_number = 12345
        mock_w3.eth.chain_id = 31337
        mock_contract = Mock()
        mock_contract.functions.isPatientRegistered.return_value.call.return_value = True
        
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            health = service.health_check()
            
            assert health['overall_status'] == 'healthy', "Should be healthy when all components work"
            assert health['blockchain']['connected'] is True
            assert health['redis']['connected'] is True
            
        # Test Redis failure only
        mock_redis.ping.side_effect = redis.ConnectionError("Redis failed")
        
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            health = service.health_check()
            
            assert health['overall_status'] == 'unhealthy', "Should be unhealthy when Redis fails"
            assert health['redis']['connected'] is False
            
        # Test blockchain failure only
        mock_redis.ping.return_value = True  # Redis works
        mock_redis.ping.side_effect = None  # Reset side effect
        mock_w3.is_connected.return_value = False
        
        with patch('core.blockchain_service.redis.Redis', return_value=mock_redis), \
             patch('core.blockchain_service.Web3', return_value=mock_w3), \
             patch.object(BlockchainService, '_load_contract', return_value=mock_contract):
            
            service = BlockchainService()
            health = service.health_check()
            
            assert health['overall_status'] == 'degraded', "Should be degraded when blockchain fails but Redis works"
            assert health['blockchain']['connected'] is False
            assert health['redis']['connected'] is True