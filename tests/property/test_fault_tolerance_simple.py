"""
Property-based tests for BlockchainService fault tolerance and caching - Task 6.8

These tests validate universal properties that must hold for blockchain service
fault tolerance and caching behavior, using Hypothesis to generate random test cases.

This file implements:
- Property 33: Blockchain Caching
- Property 34: Fault Tolerance

Validates: Requirements 9.4, 9.5
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
    """Generate valid patient ID hashes (32 bytes as hex string)"""
    hash_bytes = draw(st.binary(min_size=32, max_size=32))
    return "0x" + hash_bytes.hex()


@st.composite
def ip_hash_strategy(draw):
    """Generate valid IP hashes (32 bytes as hex string)"""
    hash_bytes = draw(st.binary(min_size=32, max_size=32))
    return "0x" + hash_bytes.hex()


class TestBlockchainCachingProperties:
    """
    Property-based tests for blockchain caching behavior.
    
    These tests validate:
    - Property 33: Blockchain Caching
    """
    
    def _create_mock_service(self, cache_ttl=300):
        """Create a properly mocked BlockchainService instance"""
        from core.blockchain_service import BlockchainService
        
        # Create service instance without calling __init__
        service = object.__new__(BlockchainService)
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.ping.return_value = True
        
        # Mock Web3 and contracts
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = True
        mock_contract = Mock()
        
        # Set required attributes
        service.w3 = mock_w3
        service.redis_client = mock_redis
        service.patient_registry = mock_contract
        service.blocked_ip_registry = mock_contract
        service.attack_signature_registry = mock_contract
        service.account = '0x1234567890123456789012345678901234567890'
        service.cache_timeout = cache_ttl
        
        return service, mock_redis, mock_contract
    
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        patient_id_hash=patient_id_hash_strategy(),
        cache_ttl=st.integers(min_value=60, max_value=3600)
    )
    def test_property_33_blockchain_caching_patient_check(self, patient_id_hash, cache_ttl):
        """
        Feature: blockchain-healthcare-security, Property 33: Blockchain Caching
        
        For any blockchain read operation performed twice within the cache TTL,
        the second read must use cached data without making an RPC call.
        
        Validates: Requirements 9.4
        """
        service, mock_redis, mock_contract = self._create_mock_service(cache_ttl)
        
        # Mock the blockchain call to return a specific result
        expected_result = True
        mock_contract.functions.isPatientRegistered.return_value.call.return_value = expected_result
        
        # First call - should hit blockchain and cache the result
        mock_redis.get.return_value = None  # No cache initially
        result1 = service.is_patient_registered(patient_id_hash)
        
        # Verify blockchain was called
        mock_contract.functions.isPatientRegistered.assert_called_once()
        
        # Verify result was cached
        cache_key = f"patient_registered:{patient_id_hash}"
        mock_redis.setex.assert_called_with(cache_key, cache_ttl, json.dumps(expected_result, default=str))
        
        # Reset mocks for second call
        mock_contract.functions.isPatientRegistered.reset_mock()
        
        # Second call within TTL - should use cache, not hit blockchain
        mock_redis.get.return_value = json.dumps(expected_result)  # Cache hit
        result2 = service.is_patient_registered(patient_id_hash)
        
        # Verify blockchain was NOT called again (cached result used)
        mock_contract.functions.isPatientRegistered.assert_not_called()
        
        # Verify both results are identical
        assert result1 == result2 == expected_result, (
            f"For any blockchain read operation performed twice within the cache TTL, "
            f"both results must be identical. Got result1={result1}, result2={result2}"
        )
    
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        ip_hash=ip_hash_strategy(),
        cache_ttl=st.integers(min_value=60, max_value=3600)
    )
    def test_property_33_blockchain_caching_ip_check(self, ip_hash, cache_ttl):
        """
        Feature: blockchain-healthcare-security, Property 33: Blockchain Caching (IP Blocking)
        
        For any IP blocking check performed twice within the cache TTL,
        the second check must use cached data without making an RPC call.
        
        Validates: Requirements 9.4
        """
        service, mock_redis, mock_contract = self._create_mock_service(cache_ttl)
        
        # Mock the blockchain call to return a specific result
        expected_result = True  # IP is blocked
        mock_contract.functions.isIPBlocked.return_value.call.return_value = expected_result
        
        # First call - should hit blockchain and cache the result
        mock_redis.get.return_value = None  # No cache initially
        result1 = service.is_ip_blocked(ip_hash)
        
        # Verify blockchain was called
        mock_contract.functions.isIPBlocked.assert_called_once()
        
        # Verify result was cached with shorter TTL for IP blocks (60 seconds)
        cache_key = f"ip_blocked:{ip_hash}"
        mock_redis.setex.assert_called_with(cache_key, 60, json.dumps(expected_result, default=str))
        
        # Reset mocks for second call
        mock_contract.functions.isIPBlocked.reset_mock()
        
        # Second call within TTL - should use cache, not hit blockchain
        mock_redis.get.return_value = json.dumps(expected_result)  # Cache hit
        result2 = service.is_ip_blocked(ip_hash)
        
        # Verify blockchain was NOT called again (cached result used)
        mock_contract.functions.isIPBlocked.assert_not_called()
        
        # Verify both results are identical
        assert result1 == result2 == expected_result, (
            f"For any IP blocking check performed twice within the cache TTL, "
            f"both results must be identical. Got result1={result1}, result2={result2}"
        )


class TestBlockchainFaultToleranceProperties:
    """
    Property-based tests for blockchain fault tolerance behavior.
    
    These tests validate:
    - Property 34: Fault Tolerance
    """
    
    def _create_mock_service_with_failure(self, cached_result=None):
        """Create a mocked BlockchainService instance with connection failure"""
        from core.blockchain_service import BlockchainService
        
        # Create service instance without calling __init__
        service = object.__new__(BlockchainService)
        
        # Mock Redis client with cached data
        mock_redis = Mock()
        if cached_result is not None:
            mock_redis.get.return_value = json.dumps(cached_result)
        else:
            mock_redis.get.return_value = None
        mock_redis.ping.return_value = True
        
        # Mock Web3 to simulate connection failure
        mock_w3 = Mock()
        mock_w3.is_connected.return_value = False  # Connection failed
        
        # Mock contract that will raise connection error
        mock_contract = Mock()
        mock_contract.functions.isPatientRegistered.return_value.call.side_effect = ProviderConnectionError("Connection failed")
        mock_contract.functions.isIPBlocked.return_value.call.side_effect = ProviderConnectionError("Connection failed")
        mock_contract.functions.getAllSignatures.return_value.call.side_effect = ProviderConnectionError("Connection failed")
        
        # Set required attributes
        service.w3 = mock_w3
        service.redis_client = mock_redis
        service.patient_registry = mock_contract
        service.blocked_ip_registry = mock_contract
        service.attack_signature_registry = mock_contract
        service.account = '0x1234567890123456789012345678901234567890'
        service.cache_timeout = 300
        
        return service, mock_redis, mock_contract
    
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
        service, mock_redis, mock_contract = self._create_mock_service_with_failure(cached_result)
        
        # Call should not crash despite blockchain connection failure
        try:
            result = service.is_patient_registered(patient_id_hash)
            
            # Should return cached result, not crash
            assert result == cached_result, (
                f"For any blockchain connection failure, the system must return cached data. "
                f"Expected {cached_result}, got {result}"
            )
            
            # Verify cache was accessed
            cache_key = f"patient_registered:{patient_id_hash}"
            mock_redis.get.assert_called_with(cache_key)
            
        except Exception as e:
            pytest.fail(
                f"For any blockchain connection failure, the system must not crash. "
                f"Got exception: {type(e).__name__}: {e}"
            )
    
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
        service, mock_redis, mock_contract = self._create_mock_service_with_failure(cached_result)
        
        # Call should not crash despite blockchain connection failure
        try:
            result = service.is_ip_blocked(ip_hash)
            
            # Should return cached result, not crash
            assert result == cached_result, (
                f"For any blockchain connection failure, the system must return cached data. "
                f"Expected {cached_result}, got {result}"
            )
            
            # Verify cache was accessed
            cache_key = f"ip_blocked:{ip_hash}"
            mock_redis.get.assert_called_with(cache_key)
            
        except Exception as e:
            pytest.fail(
                f"For any blockchain connection failure, the system must not crash. "
                f"Got exception: {type(e).__name__}: {e}"
            )
    
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        operation_type=st.sampled_from(['patient_check', 'ip_check', 'attack_signatures'])
    )
    def test_property_34_fault_tolerance_no_cache(self, operation_type):
        """
        Feature: blockchain-healthcare-security, Property 34: Fault Tolerance (No Cache Available)
        
        For any blockchain connection failure when no cached data is available,
        the system must return a safe default value and must not crash.
        
        Validates: Requirements 9.5
        """
        service, mock_redis, mock_contract = self._create_mock_service_with_failure(cached_result=None)
        
        # Test different operation types
        test_hash = "0x" + ("a" * 64)  # Valid hex hash
        
        try:
            if operation_type == 'patient_check':
                result = service.is_patient_registered(test_hash)
                # Should return False (safe default) when no cache and blockchain fails
                assert result is False, (
                    f"Patient check should return False (safe default) when blockchain fails and no cache available"
                )
                
            elif operation_type == 'ip_check':
                result = service.is_ip_blocked(test_hash)
                # Should return False (safe default) when no cache and blockchain fails
                assert result is False, (
                    f"IP check should return False (safe default) when blockchain fails and no cache available"
                )
                
            elif operation_type == 'attack_signatures':
                result = service.get_attack_signatures()
                # Should return empty list (safe default) when no cache and blockchain fails
                assert result == [], (
                    f"Attack signatures should return empty list (safe default) when blockchain fails and no cache available"
                )
            
        except Exception as e:
            pytest.fail(
                f"For any blockchain connection failure, the system must not crash even without cache. "
                f"Operation: {operation_type}, "
                f"Got exception: {type(e).__name__}: {e}"
            )
    
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
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
        
        # Create service instance without calling __init__
        service = object.__new__(BlockchainService)
        
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
        if not blockchain_failure:
            mock_w3.eth.block_number = 12345
            mock_w3.eth.chain_id = 31337
        
        # Mock contract behavior
        mock_contract = Mock()
        if blockchain_failure:
            mock_contract.functions.isPatientRegistered.return_value.call.side_effect = ProviderConnectionError("Blockchain failed")
        else:
            mock_contract.functions.isPatientRegistered.return_value.call.return_value = True
        
        # Set required attributes
        service.w3 = mock_w3
        service.redis_client = mock_redis
        service.patient_registry = mock_contract
        service.blocked_ip_registry = mock_contract
        service.attack_signature_registry = mock_contract
        service.account = '0x1234567890123456789012345678901234567890'
        service.cache_timeout = 300
        
        try:
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
