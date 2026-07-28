"""
ThreatScoreCalculator for multi-factor DDoS detection.
Analyzes request patterns to detect sophisticated distributed attacks.
"""

import json
import logging
import math
from typing import Dict, List, Optional, Tuple, Any

import redis
from django.conf import settings
from django.http import HttpRequest

from .blockchain_service import get_blockchain_service

logger = logging.getLogger('security')


class ThreatScoreCalculator:
    """
    Multi-factor threat scoring engine that analyzes request patterns
    to detect DDoS attacks beyond simple IP rate limiting.
    """
    
    def __init__(self, redis_client=None, blockchain_service=None):
        """
        Initialize threat calculator with dependencies.
        
        Args:
            redis_client: Redis client for caching and rate tracking
            blockchain_service: Blockchain service for attack signatures
        """
        # Initialize Redis client
        if redis_client is None:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
        else:
            self.redis = redis_client
        
        # Initialize blockchain service
        if blockchain_service is None:
            self.blockchain = get_blockchain_service()
        else:
            self.blockchain = blockchain_service
        
        # Threat score thresholds from settings
        self.thresholds = settings.THREAT_SCORE_THRESHOLDS
        
        logger.info("ThreatScoreCalculator initialized")
    
    def calculate_threat_score(self, request: HttpRequest, ip_address: str) -> Tuple[int, Dict[str, int]]:
        """
        Calculate comprehensive threat score (0-100) based on multiple factors.
        
        Args:
            request: Django HTTP request object
            ip_address: Client IP address
            
        Returns:
            Tuple of (total_score, factor_breakdown)
        """
        try:
            logger.debug(f"Calculating threat score for IP: {ip_address}")
            
            factors = {}
            
            # Factor 1: Request rate (0-20 points)
            factors['rate'] = self._calculate_rate_score(ip_address)
            
            # Factor 2: Pattern repetition (0-25 points)
            factors['pattern'] = self._calculate_pattern_score(ip_address, request)
            
            # Factor 3: Session behavior (0-20 points)
            factors['session'] = self._calculate_session_score(request)
            
            # Factor 4: User-Agent entropy (0-15 points)
            factors['entropy'] = self._calculate_entropy_score(ip_address, request)
            
            # Factor 5: Authentication failures (0-10 points)
            factors['auth_failures'] = self._calculate_auth_failure_score(ip_address)
            
            # Factor 6: Known attack signature match (0-30 points)
            factors['signature_match'] = self._check_attack_signatures(ip_address, request)
            
            # Calculate total score (capped at 100)
            total_score = sum(factors.values())
            total_score = min(total_score, 100)
            
            logger.debug(f"Threat score for {ip_address}: {total_score} (factors: {factors})")
            
            return total_score, factors
            
        except Exception as e:
            logger.error(f"Error calculating threat score for {ip_address}: {e}")
            # Return safe default values
            return 0, {
                'rate': 0,
                'pattern': 0,
                'session': 0,
                'entropy': 0,
                'auth_failures': 0,
                'signature_match': 0
            }
    
    def _calculate_rate_score(self, ip_address: str) -> int:
        """
        Calculate threat score based on request rate per minute.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Rate score (0-20 points)
        """
        try:
            # Use Redis key with 1-minute sliding window
            key = f"rate:{ip_address}"
            
            # Increment request count for this IP
            count = self.redis.incr(key)
            
            # Set expiry on first request (when count == 1)
            if count == 1:
                self.redis.expire(key, 60)  # 1 minute window
            
            logger.debug(f"Request rate for {ip_address}: {count} requests/minute")
            
            # Base score based on request rate thresholds
            # Requirements 2.2: >100 requests/minute = 20 points
            base_score = 0
            if count > 100:
                base_score = 20
            elif count > 80:
                base_score = 18
            elif count > 60:
                base_score = 15
            elif count > 40:
                base_score = 12
            elif count > 30:
                base_score = 8
            elif count > 20:
                base_score = 5
            elif count > 15:
                base_score = 3
            else:
                base_score = 0
            
            # Add threat boost from rate limit violations
            # Requirements 10.5: Increase threat score for repeat violations
            threat_boost = self._get_rate_limit_threat_boost(ip_address)
            total_score = base_score + threat_boost
            
            # Cap at maximum rate score
            total_score = min(total_score, 20)
            
            if threat_boost > 0:
                logger.debug(f"Rate score for {ip_address}: {base_score} + {threat_boost} boost = {total_score}")
            
            return total_score
                
        except Exception as e:
            logger.error(f"Error calculating rate score for {ip_address}: {e}")
            return 0
    
    def _calculate_pattern_score(self, ip_address: str, request: HttpRequest) -> int:
        """
        Calculate threat score based on endpoint access patterns.
        
        Args:
            ip_address: Client IP address
            request: Django HTTP request object
            
        Returns:
            Pattern score (0-25 points)
        """
        try:
            # Use Redis list to track last 20 endpoints per IP
            key = f"pattern:{ip_address}"
            endpoint = request.path.lstrip('/')  # Remove leading slash for pattern analysis
            
            # Add current endpoint to the list
            self.redis.lpush(key, endpoint)
            
            # Keep only last 20 requests
            self.redis.ltrim(key, 0, 19)
            
            # Set expiry for 5 minutes
            self.redis.expire(key, 300)
            
            # Get all tracked endpoints for this IP
            endpoints = self.redis.lrange(key, 0, -1)
            
            # Need at least 10 requests to calculate meaningful pattern
            if len(endpoints) < 10:
                logger.debug(f"Insufficient requests ({len(endpoints)}) for pattern analysis: {ip_address}")
                return 0
            
            # Calculate endpoint diversity ratio
            unique_endpoints = len(set(endpoints))
            total_requests = len(endpoints)
            diversity_ratio = unique_endpoints / total_requests
            repetition_ratio = 1 - diversity_ratio
            
            logger.debug(f"Pattern analysis for {ip_address}: {unique_endpoints}/{total_requests} unique endpoints, repetition ratio: {repetition_ratio:.2f}")
            
            # Score based on repetition ratio
            # Requirements 2.3: >80% same endpoint = 25 points
            if repetition_ratio > 0.8:  # 80% same endpoint
                return 25
            elif repetition_ratio > 0.7:  # 70% same endpoint
                return 20
            elif repetition_ratio > 0.6:  # 60% same endpoint
                return 15
            elif repetition_ratio > 0.5:  # 50% same endpoint
                return 10
            elif repetition_ratio > 0.4:  # 40% same endpoint
                return 5
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating pattern score for {ip_address}: {e}")
            return 0
    
    def _calculate_session_score(self, request: HttpRequest) -> int:
        """
        Calculate threat score based on session and authentication status.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            Session score (0-20 points)
        """
        try:
            # Check authentication status
            is_authenticated = request.user.is_authenticated
            
            # Check for session cookies
            has_session = bool(request.session.session_key)
            
            # Check for any cookies
            has_cookies = bool(request.COOKIES)
            
            # Check for common authentication headers
            has_auth_header = bool(
                request.META.get('HTTP_AUTHORIZATION') or
                request.META.get('HTTP_X_API_KEY') or
                request.META.get('HTTP_X_AUTH_TOKEN')
            )
            
            logger.debug(f"Session analysis - Auth: {is_authenticated}, Session: {has_session}, Cookies: {has_cookies}, Auth header: {has_auth_header}")
            
            # Requirements 2.4: No session cookies or authentication = 20 points
            if is_authenticated:
                # Authenticated users get no penalty
                return 0
            elif has_auth_header:
                # API authentication present
                return 0
            elif not has_session and not has_cookies:
                # No session or cookies = likely bot
                return 20
            elif not has_session:
                # Has cookies but no session = suspicious
                return 15
            elif len(request.COOKIES) < 2:
                # Very few cookies = suspicious
                return 10
            else:
                # Has session and multiple cookies = likely legitimate
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating session score: {e}")
            return 0
    
    def _calculate_entropy_score(self, ip_address: str, request: HttpRequest) -> int:
        """
        Calculate threat score based on User-Agent entropy and variety.
        
        Args:
            ip_address: Client IP address
            request: Django HTTP request object
            
        Returns:
            Entropy score (0-15 points)
        """
        try:
            # Get User-Agent from request
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if not user_agent:
                # No User-Agent = suspicious
                return 15
            
            # Track User-Agent variety for this IP using Redis set
            key = f"ua:{ip_address}"
            
            # Add current User-Agent to set
            self.redis.sadd(key, user_agent)
            
            # Set expiry for 1 hour
            self.redis.expire(key, 3600)
            
            # Get all User-Agents seen from this IP
            user_agents = self.redis.smembers(key)
            ua_count = len(user_agents)
            
            logger.debug(f"User-Agent analysis for {ip_address}: {ua_count} unique UAs")
            
            # Requirements 2.5: Low entropy (below 2.0) = 15 points
            # We'll use variety count as a proxy for entropy
            if ua_count == 0:
                # No User-Agents recorded (shouldn't happen)
                return 15
            elif ua_count == 1:
                # Always same User-Agent = likely bot
                return 15
            elif ua_count > 10:
                # Too many different User-Agents = suspicious
                return 12
            elif ua_count > 5:
                # Many different User-Agents = somewhat suspicious
                return 8
            else:
                # Reasonable variety (2-5 UAs) = normal behavior
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating entropy score for {ip_address}: {e}")
            return 0
    
    def _calculate_auth_failure_score(self, ip_address: str) -> int:
        """
        Calculate threat score based on failed authentication attempts.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Auth failure score (0-10 points)
        """
        try:
            # Track failed login attempts for this IP
            key = f"auth_fail:{ip_address}"
            
            # Get current failure count
            failures = self.redis.get(key)
            
            if failures is None:
                # No failures recorded
                return 0
            
            failures = int(failures)
            
            logger.debug(f"Auth failure analysis for {ip_address}: {failures} failures")
            
            # Requirements 2.6: >5 failures in 10 minutes = 10 points
            if failures > 10:
                return 10
            elif failures > 5:
                return 10  # Requirements specify >5 failures = 10 points
            elif failures > 3:
                return 7
            elif failures > 1:
                return 3
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating auth failure score for {ip_address}: {e}")
            return 0
    
    def record_auth_failure(self, ip_address: str) -> None:
        """
        Record an authentication failure for an IP address.
        
        Args:
            ip_address: Client IP address that failed authentication
        """
        try:
            key = f"auth_fail:{ip_address}"
            
            # Increment failure count
            count = self.redis.incr(key)
            
            # Set expiry on first failure (when count == 1)
            if count == 1:
                self.redis.expire(key, 600)  # 10 minutes window
            
            logger.info(f"Recorded auth failure for {ip_address}: {count} total failures")
            
        except Exception as e:
            logger.error(f"Error recording auth failure for {ip_address}: {e}")
    
    def clear_auth_failures(self, ip_address: str) -> None:
        """
        Clear authentication failures for an IP address (e.g., after successful login).
        
        Args:
            ip_address: Client IP address to clear failures for
        """
        try:
            key = f"auth_fail:{ip_address}"
            self.redis.delete(key)
            logger.debug(f"Cleared auth failures for {ip_address}")
            
        except Exception as e:
            logger.error(f"Error clearing auth failures for {ip_address}: {e}")
    
    def _get_rate_limit_threat_boost(self, ip_address: str) -> int:
        """
        Get threat score boost for IP addresses that have violated rate limits.
        This integrates with the rate limiting system to increase scores for repeat offenders.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Threat boost score (0-15 points)
        """
        try:
            threat_key = f"threat_boost:{ip_address}"
            boost = self.redis.get(threat_key)
            
            if boost is None:
                return 0
            
            return int(boost)
            
        except Exception as e:
            logger.error(f"Error getting rate limit threat boost for {ip_address}: {e}")
            return 0
    
    def _check_attack_signatures(self, ip_address: str, request: HttpRequest) -> int:
        """
        Check if request matches known attack signatures from blockchain.
        
        Args:
            ip_address: Client IP address
            request: Django HTTP request object
            
        Returns:
            Signature match score (0-30 points)
        """
        try:
            # Get attack signatures from blockchain (with caching)
            signatures = self.blockchain.get_attack_signatures()
            
            if not signatures:
                logger.debug("No attack signatures available for matching")
                return 0
            
            # Check each signature for a match
            for signature in signatures:
                if self._matches_signature(ip_address, request, signature):
                    severity = signature.get('severity', 5)
                    
                    # Requirements 5.5: Signature match = 30 points
                    # Scale based on severity (1-10)
                    score = min(30, severity * 3)
                    
                    logger.warning(f"Attack signature match for {ip_address}: {signature['hash'][:16]}... (severity: {severity}, score: {score})")
                    return score
            
            # No signature matches
            return 0
            
        except Exception as e:
            logger.error(f"Error checking attack signatures for {ip_address}: {e}")
            return 0
    
    def _matches_signature(self, ip_address: str, request: HttpRequest, signature: Dict) -> bool:
        """
        Check if current request matches a specific attack signature.
        
        Args:
            ip_address: Client IP address
            request: Django HTTP request object
            signature: Attack signature dictionary from blockchain
            
        Returns:
            True if request matches signature, False otherwise
        """
        try:
            pattern = signature.get('pattern', {})
            
            if not isinstance(pattern, dict):
                logger.warning(f"Invalid signature pattern format: {type(pattern)}")
                return False
            
            # Check endpoint pattern
            if 'endpoint_pattern' in pattern:
                endpoint_pattern = pattern['endpoint_pattern']
                if isinstance(endpoint_pattern, str):
                    if endpoint_pattern in request.path:
                        logger.debug(f"Endpoint pattern match: {endpoint_pattern}")
                    else:
                        return False
            
            # Check method pattern
            if 'method' in pattern:
                if pattern['method'] != request.method:
                    return False
            
            # Check User-Agent pattern
            if 'user_agent_pattern' in pattern:
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                ua_pattern = pattern['user_agent_pattern']
                if isinstance(ua_pattern, str):
                    if ua_pattern not in user_agent:
                        return False
            
            # Check rate pattern (requests per minute)
            if 'min_rate' in pattern:
                rate_key = f"rate:{ip_address}"
                current_rate = self.redis.get(rate_key)
                if current_rate is None or int(current_rate) < pattern['min_rate']:
                    return False
            
            # Check repetition pattern
            if 'min_repetition_ratio' in pattern:
                pattern_key = f"pattern:{ip_address}"
                endpoints = self.redis.lrange(pattern_key, 0, -1)
                if len(endpoints) >= 10:
                    unique_endpoints = len(set(endpoints))
                    repetition_ratio = 1 - (unique_endpoints / len(endpoints))
                    if repetition_ratio < pattern['min_repetition_ratio']:
                        return False
            
            # Check query parameter patterns
            if 'query_params' in pattern:
                query_params = pattern['query_params']
                if isinstance(query_params, dict):
                    for param, expected_value in query_params.items():
                        if request.GET.get(param) != expected_value:
                            return False
            
            # Check header patterns
            if 'headers' in pattern:
                headers = pattern['headers']
                if isinstance(headers, dict):
                    for header, expected_value in headers.items():
                        header_key = f"HTTP_{header.upper().replace('-', '_')}"
                        if request.META.get(header_key) != expected_value:
                            return False
            
            # If we get here, all pattern checks passed
            logger.debug(f"Full signature match for IP {ip_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error matching signature for {ip_address}: {e}")
            return False
    
    def get_threat_level(self, threat_score: int) -> str:
        """
        Convert threat score to threat level classification.
        
        Args:
            threat_score: Numerical threat score (0-100)
            
        Returns:
            Threat level string ('LOW', 'MEDIUM', 'HIGH')
        """
        if threat_score >= self.thresholds['HIGH']:
            return 'HIGH'
        elif threat_score >= self.thresholds['MEDIUM']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def should_block_request(self, threat_score: int) -> bool:
        """
        Determine if request should be blocked based on threat score.
        
        Args:
            threat_score: Numerical threat score (0-100)
            
        Returns:
            True if request should be blocked, False otherwise
        """
        return threat_score >= self.thresholds['HIGH']
    
    def should_require_captcha(self, threat_score: int) -> bool:
        """
        Determine if request should require CAPTCHA based on threat score.
        
        Args:
            threat_score: Numerical threat score (0-100)
            
        Returns:
            True if CAPTCHA should be required, False otherwise
        """
        return (self.thresholds['MEDIUM'] <= threat_score < self.thresholds['HIGH'])


# Singleton instance for global use
_threat_calculator = None

def get_threat_calculator() -> ThreatScoreCalculator:
    """
    Get singleton instance of ThreatScoreCalculator.
    
    Returns:
        ThreatScoreCalculator instance
    """
    global _threat_calculator
    if _threat_calculator is None:
        _threat_calculator = ThreatScoreCalculator()
    return _threat_calculator