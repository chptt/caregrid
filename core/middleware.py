"""
SecurityMiddleware for MediChain blockchain healthcare security system.
Intercepts all requests and performs threat analysis, blocking high-threat requests
and challenging medium-threat requests with CAPTCHA.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import redis
from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from web3 import Web3

from .blockchain_service import get_blockchain_service
from .threat_calculator import get_threat_calculator
from .anomaly_detector import AnomalyDetector
from firewall.models import SecurityLog, BlockedIP

logger = logging.getLogger('security')


class SecurityMiddleware:
    """
    Middleware that intercepts all requests and performs threat analysis.
    Blocks high-threat requests and challenges medium-threat requests.
    """
    
    def __init__(self, get_response):
        """
        Initialize SecurityMiddleware with dependencies.
        
        Args:
            get_response: Django get_response callable
        """
        self.get_response = get_response
        
        # Initialize Redis client for caching and rate limiting
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Test Redis connection
            self.redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - using in-memory fallback")
            self.redis = None
        
        # Initialize blockchain service and threat calculator
        self.blockchain = get_blockchain_service()
        self.threat_calculator = get_threat_calculator()
        
        # Initialize anomaly detector for coordinated attack detection
        self.anomaly_detector = AnomalyDetector(self.redis, self.blockchain)
        
        # Load configuration from settings
        self.thresholds = settings.THREAT_SCORE_THRESHOLDS
        self.auto_block_duration = settings.AUTO_BLOCK_DURATION
        self.captcha_failure_block_duration = settings.CAPTCHA_FAILURE_BLOCK_DURATION
        self.captcha_max_failures = settings.CAPTCHA_MAX_FAILURES
        
        logger.info("SecurityMiddleware initialized")
    
    def __call__(self, request):
        """
        Process request through middleware.
        """
        # Process request first
        response = self.process_request(request)
        if response:
            return response
        
        # Continue to view
        response = self.get_response(request)
        return response
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process incoming request and perform security analysis.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse if request should be blocked/challenged, None to continue
        """
        try:
            # Skip security check for admin, static files, and health checks
            if self._should_skip_security_check(request):
                return None
            
            # Extract client IP address
            ip_address = self._get_client_ip(request)
            ip_hash = Web3.keccak(text=ip_address).hex()
            
            logger.debug(f"Processing request from IP: {ip_address} to {request.path}")
            
            # Check blockchain blocklist first (Requirements 4.3, 4.4)
            # This is the primary security gate - if IP is blocked on blockchain,
            # reject immediately with 403 status (Requirements 4.4)
            if self._is_ip_blocked_on_blockchain(ip_hash):
                logger.warning(f"Blocked request from blockchain-blocked IP: {ip_address}")
                # Update security log to reflect blockchain block
                self._log_blockchain_block_event(request, ip_address)
                return self._create_blocked_response("IP blocked due to security policy")
            
            # Calculate threat score for this request
            threat_score, factors = self.threat_calculator.calculate_threat_score(request, ip_address)
            
            # Analyze request pattern for coordinated attack detection (Requirements 5.1, 5.2)
            attack_signature_hash = None
            if self.redis:  # Only if Redis is available
                try:
                    attack_signature_hash = self.anomaly_detector.analyze_request_pattern(ip_address, request)
                    if attack_signature_hash:
                        logger.warning(f"Coordinated attack detected from {ip_address}: {attack_signature_hash}")
                        # Boost threat score for coordinated attack (Requirements 5.5)
                        threat_score = min(100, threat_score + 30)
                        factors['coordinated_attack'] = 30
                except Exception as e:
                    logger.error(f"Error in anomaly detection for {ip_address}: {e}")
            
            # Track CAPTCHA verification status for logging
            captcha_verified = False
            
            # Take action based on threat level (Requirements 2.7, 2.8, 2.9)
            # Requirements specify:
            # - Score >= 60: High threat (block)
            # - Score 40-59: Medium threat (CAPTCHA)  
            # - Score < 40: Low threat (allow)
            
            if threat_score >= 80:
                # Very high threat - auto-block on blockchain (Requirements 11.1, 11.2)
                logger.warning(f"Very high threat - auto-blocking: {ip_address} (score: {threat_score})")
                # Log security event before auto-blocking
                self._log_security_event(request, ip_address, threat_score, factors, captcha_verified=False)
                self._auto_block_ip(ip_address, ip_hash, threat_score)
                return self._create_blocked_response("Suspicious activity detected - IP blocked")
            
            elif threat_score >= self.thresholds['HIGH']:  # >= 60
                # High threat - block but don't auto-add to blockchain (Requirements 2.7)
                logger.warning(f"High threat request blocked: {ip_address} (score: {threat_score})")
                # Log security event before blocking
                self._log_security_event(request, ip_address, threat_score, factors, captcha_verified=False)
                return self._create_blocked_response("Multiple security violations detected")
            
            elif threat_score >= self.thresholds['MEDIUM']:  # 40-59
                # Medium threat - require CAPTCHA (Requirements 2.8, 6.1)
                if not self._verify_captcha(request, ip_address):
                    logger.info(f"CAPTCHA required for medium threat: {ip_address} (score: {threat_score})")
                    # Log security event before returning CAPTCHA response
                    self._log_security_event(request, ip_address, threat_score, factors, captcha_verified=False)
                    return self._create_captcha_response(threat_score)
                else:
                    logger.info(f"CAPTCHA verified, allowing medium threat request: {ip_address}")
                    captcha_verified = True
            
            # Low threat (< 40) or CAPTCHA passed - allow request (Requirements 2.9)
            logger.debug(f"Request allowed: {ip_address} (score: {threat_score})")
            
            # Log security event (Requirements 3.1, 3.2)
            self._log_security_event(request, ip_address, threat_score, factors, captcha_verified=captcha_verified)
            
            # Store threat information in request for use by views
            request.threat_score = threat_score
            request.threat_factors = factors
            request.client_ip = ip_address
            
            return None  # Continue processing
            
        except Exception as e:
            logger.error(f"SecurityMiddleware error: {e}")
            # On error, allow request to continue (fail open for availability)
            return None
    
    def _should_skip_security_check(self, request: HttpRequest) -> bool:
        """
        Determine if security check should be skipped for this request.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            True if security check should be skipped, False otherwise
        """
        # Skip paths that don't need security analysis
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/health/',
            '/api/health/',
            '/api/security/captcha/',  # Skip CAPTCHA endpoints
            '/__debug__/',  # Django debug toolbar
        ]
        
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return True
        
        for skip_path in skip_paths:
            if request.path.startswith(skip_path):
                return True
        
        return False
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Extract client IP address from request headers.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            Client IP address as string
        """
        # Check for forwarded IP first (for load balancers/proxies)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Direct connection
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        return ip
    def _is_ip_blocked_on_blockchain(self, ip_hash: str) -> bool:
        """
        Check if IP is blocked on blockchain (Requirements 4.3, 4.4).
        
        This method implements the core blockchain blocklist checking functionality:
        - Queries the blockchain BlockedIPRegistry contract
        - Falls back to local database if blockchain is unavailable
        - Handles expired blocks automatically
        
        Args:
            ip_hash: Hashed IP address (bytes32 hex string)
            
        Returns:
            True if IP is blocked, False otherwise
        """
        try:
            # Primary check: Query blockchain directly (Requirements 4.3)
            is_blocked = self.blockchain.is_ip_blocked(ip_hash)
            
            if is_blocked:
                logger.info(f"IP {ip_hash[:16]}... is blocked on blockchain")
                return True
            
            # Also check for temporary local blocks (CAPTCHA failures, etc.)
            ip_address = self._get_ip_from_hash(ip_hash)
            if ip_address and self._is_temporarily_blocked(ip_address):
                logger.info(f"IP {ip_address} is temporarily blocked locally")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking blockchain blocklist for {ip_hash}: {e}")
            
            # Fallback: Check local database for blockchain-synced blocks
            try:
                from django.utils import timezone
                
                # Check for non-expired blocks in local database
                blocked_ip = BlockedIP.objects.filter(
                    ip_hash=ip_hash,
                    expiry_time__gt=timezone.now(),
                    blockchain_synced=True  # Only consider blockchain-synced blocks
                ).first()
                
                if blocked_ip:
                    logger.warning(f"Using local database fallback: IP {blocked_ip.ip_address} is blocked")
                    return True
                
                # Also check temporary local blocks
                ip_address = self._get_ip_from_hash(ip_hash)
                if ip_address and self._is_temporarily_blocked(ip_address):
                    return True
                
                return False
                
            except Exception as db_error:
                logger.error(f"Error checking local blocklist fallback: {db_error}")
                # On complete failure, err on the side of availability (don't block)
                return False
    
    def _get_ip_from_hash(self, ip_hash: str) -> Optional[str]:
        """
        Get IP address from hash by looking up in local database.
        
        Args:
            ip_hash: Hashed IP address
            
        Returns:
            IP address string or None if not found
        """
        try:
            blocked_ip = BlockedIP.objects.filter(ip_hash=ip_hash).first()
            return blocked_ip.ip_address if blocked_ip else None
        except Exception as e:
            logger.error(f"Error looking up IP from hash: {e}")
            return None
    
    def _log_security_event(self, request: HttpRequest, ip_address: str, 
                           threat_score: int, factors: Dict[str, int], captcha_verified: bool = False) -> None:
        """
        Log security event to database (Requirements 3.1, 3.2).
        
        This method implements comprehensive security logging:
        - Logs all requests with IP, timestamp, endpoint, User-Agent (Requirements 3.1)
        - Stores threat score and all factor breakdowns (Requirements 3.2)
        - Records action taken for audit trail
        - Includes blockchain sync status for blocked IPs
        
        Args:
            request: Django HTTP request object
            ip_address: Client IP address
            threat_score: Calculated threat score
            factors: Breakdown of threat factors
            captcha_verified: Whether CAPTCHA was successfully verified for this request
        """
        try:
            # Determine threat level based on score
            threat_level = self.threat_calculator.get_threat_level(threat_score)
            
            # Determine action taken based on threat score and CAPTCHA verification
            if threat_score >= 80:
                action_taken = 'auto_blocked'
                blocked_on_blockchain = True
            elif threat_score >= self.thresholds['HIGH']:
                action_taken = 'blocked'
                blocked_on_blockchain = False
            elif threat_score >= self.thresholds['MEDIUM']:
                # For medium threat, check if CAPTCHA was verified
                if captcha_verified:
                    action_taken = 'allowed'  # CAPTCHA was verified, request allowed
                else:
                    action_taken = 'captcha'  # CAPTCHA required
                blocked_on_blockchain = False
            else:
                action_taken = 'allowed'
                blocked_on_blockchain = False
            
            # Extract additional request metadata
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            referer = request.META.get('HTTP_REFERER', '')
            content_type = request.META.get('CONTENT_TYPE', '')
            
            # Create comprehensive security log entry (Requirements 3.1, 3.2)
            security_log = SecurityLog.objects.create(
                # Basic request information (Requirements 3.1)
                ip_address=ip_address,
                endpoint=request.path,
                method=request.method,
                user_agent=user_agent,
                
                # Threat analysis results (Requirements 3.2)
                threat_score=threat_score,
                threat_level=threat_level,
                
                # Individual threat factor scores (Requirements 3.2)
                rate_score=factors.get('rate', 0),
                pattern_score=factors.get('pattern', 0),
                session_score=factors.get('session', 0),
                entropy_score=factors.get('entropy', 0),
                auth_failure_score=factors.get('auth_failures', 0),
                
                # Action taken and blockchain status
                action_taken=action_taken,
                blocked_on_blockchain=blocked_on_blockchain
            )
            
            # Log summary for monitoring
            logger.info(f"Security event logged: {ip_address} -> {request.method} {request.path} "
                       f"(score: {threat_score}, level: {threat_level}, action: {action_taken})")
            
            # Additional debug logging for high-threat events
            if threat_score >= self.thresholds['MEDIUM']:
                logger.warning(f"High threat event details: IP={ip_address}, "
                              f"factors={factors}, UA='{user_agent[:100]}...'")
            
            return security_log
            
        except Exception as e:
            logger.error(f"Error logging security event for {ip_address}: {e}")
            # Security logging failure should not break request processing
            return None
    
    def _auto_block_ip(self, ip_address: str, ip_hash: str, threat_score: int) -> None:
        """
        Automatically block IP on blockchain and local database (Requirements 11.1, 11.2).
        
        This method implements automatic blocking for very high threat scores (>= 80):
        - Writes IP to blockchain BlockedIPRegistry with 24-hour expiry (Requirements 11.1)
        - Stores block in local database for fallback and audit trail (Requirements 11.2)
        - Sets automatic expiry time (Requirements 11.2)
        - Handles blockchain failures gracefully
        
        Args:
            ip_address: Client IP address
            ip_hash: Hashed IP address (bytes32 hex string)
            threat_score: Threat score that triggered the block
        """
        try:
            from django.utils import timezone
            
            # Calculate expiry time (24 hours from now) - Requirements 11.2
            expiry_time = timezone.now() + timedelta(seconds=self.auto_block_duration)
            
            reason = f"Auto-blocked: threat score {threat_score} (threshold: 80)"
            
            logger.warning(f"Auto-blocking IP {ip_address}: {reason}")
            
            # Step 1: Add to blockchain first (Requirements 11.1)
            blockchain_success = False
            tx_hash = None
            
            try:
                tx_hash, blockchain_success = self.blockchain.block_ip(
                    ip_hash,
                    self.auto_block_duration,  # 24 hours in seconds
                    reason,
                    is_manual=False  # This is an automatic block
                )
                
                if blockchain_success:
                    logger.info(f"IP {ip_address} successfully blocked on blockchain (tx: {tx_hash})")
                else:
                    logger.error(f"Failed to block IP {ip_address} on blockchain")
                    
            except Exception as blockchain_error:
                logger.error(f"Blockchain blocking failed for {ip_address}: {blockchain_error}")
                blockchain_success = False
            
            # Step 2: Add to local database (Requirements 11.2)
            try:
                # Check if already exists to avoid duplicates
                existing_block = BlockedIP.objects.filter(ip_address=ip_address).first()
                
                if existing_block:
                    # Update existing block
                    existing_block.expiry_time = expiry_time
                    existing_block.reason = reason
                    existing_block.blockchain_synced = blockchain_success
                    existing_block.block_tx_hash = tx_hash or ''
                    existing_block.save()
                    logger.info(f"Updated existing block for IP {ip_address}")
                else:
                    # Create new block entry
                    BlockedIP.objects.create(
                        ip_address=ip_address,
                        ip_hash=ip_hash,
                        expiry_time=expiry_time,
                        reason=reason,
                        is_manual=False,  # Automatic block
                        blockchain_synced=blockchain_success,
                        block_tx_hash=tx_hash or ''
                    )
                    logger.info(f"IP {ip_address} added to local blocklist")
                
            except Exception as db_error:
                logger.error(f"Error adding IP to local blocklist: {db_error}")
            
            # Step 3: Update security log with block transaction hash
            try:
                if tx_hash:
                    # Find the most recent security log for this IP and update it
                    recent_log = SecurityLog.objects.filter(
                        ip_address=ip_address,
                        action_taken='auto_blocked'
                    ).order_by('-timestamp').first()
                    
                    if recent_log:
                        recent_log.block_tx_hash = tx_hash
                        recent_log.save()
                        
            except Exception as log_error:
                logger.error(f"Error updating security log with tx hash: {log_error}")
            
            # Step 4: Clear any cached data for this IP
            try:
                self._clear_ip_caches(ip_address)
            except Exception as cache_error:
                logger.error(f"Error clearing caches for {ip_address}: {cache_error}")
            
            # Log final status
            if blockchain_success:
                logger.warning(f"Auto-block completed successfully: {ip_address} blocked on blockchain and locally")
            else:
                logger.warning(f"Auto-block partially completed: {ip_address} blocked locally only (blockchain failed)")
                
        except Exception as e:
            logger.error(f"Critical error auto-blocking IP {ip_address}: {e}")
    
    def _clear_ip_caches(self, ip_address: str) -> None:
        """
        Clear all cached data for an IP address after blocking.
        
        Args:
            ip_address: Client IP address
        """
        try:
            # Clear threat calculation caches
            cache_keys = [
                f"rate:{ip_address}",
                f"pattern:{ip_address}",
                f"ua:{ip_address}",
                f"auth_fail:{ip_address}",
                f"captcha_failures:{ip_address}",
                f"temp_blocked:{ip_address}"
            ]
            
            for key in cache_keys:
                self.redis.delete(key)
            
            logger.debug(f"Cleared caches for blocked IP: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error clearing caches for {ip_address}: {e}")
    
    def _verify_captcha(self, request: HttpRequest, ip_address: str) -> bool:
        """
        Verify CAPTCHA response (Requirements 6.2, 6.3).
        
        This method implements comprehensive CAPTCHA verification:
        - Checks CAPTCHA tokens stored in Redis (Requirements 6.2)
        - Tracks CAPTCHA failures and blocks after 3 failures (Requirements 6.3)
        - Exempts authenticated users with established sessions (Requirements 6.5)
        - Reduces threat score after successful CAPTCHA (Requirements 6.4)
        
        Args:
            request: Django HTTP request object
            ip_address: Client IP address
            
        Returns:
            True if CAPTCHA is valid or not required, False if CAPTCHA required/failed
        """
        try:
            # Check if user is authenticated with established session (Requirements 6.5)
            if request.user.is_authenticated:
                session_age = self._get_session_age(request)
                if session_age and session_age > 300:  # 5 minutes of established session
                    logger.debug(f"CAPTCHA exemption for authenticated user: {request.user} (session age: {session_age}s)")
                    return True
            
            # Check for CAPTCHA token in headers
            captcha_token = request.META.get('HTTP_X_CAPTCHA_TOKEN')
            if not captcha_token:
                # Also check in POST data for form submissions
                captcha_token = request.POST.get('captcha_token') if hasattr(request, 'POST') else None
            
            if not captcha_token:
                # No CAPTCHA token provided - CAPTCHA required
                logger.debug(f"No CAPTCHA token provided for {ip_address}")
                return False
            
            # Verify token exists in Redis and matches this IP (Requirements 6.2)
            captcha_key = f"captcha:{captcha_token}"
            stored_data = self.redis.get(captcha_key)
            
            if stored_data:
                try:
                    # Parse stored CAPTCHA data (JSON format)
                    captcha_data = json.loads(stored_data)
                    stored_ip = captcha_data.get('ip_address')
                    created_time = captcha_data.get('created_time', 0)
                    
                    # Verify IP matches and token hasn't expired (5 minutes)
                    current_time = datetime.now().timestamp()
                    if (stored_ip == ip_address and 
                        current_time - created_time < 300):  # 5 minute expiry
                        
                        # Valid CAPTCHA token for this IP
                        self.redis.delete(captcha_key)  # Use token only once
                        
                        # Clear CAPTCHA failure count on success
                        failure_key = f"captcha_failures:{ip_address}"
                        self.redis.delete(failure_key)
                        
                        # Reduce threat score for subsequent requests (Requirements 6.4)
                        self._reduce_threat_score_for_captcha_success(ip_address)
                        
                        logger.info(f"CAPTCHA verification successful for {ip_address}")
                        return True
                    else:
                        logger.warning(f"CAPTCHA token mismatch or expired for {ip_address}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid CAPTCHA data format for token {captcha_token}")
            
            # Invalid, expired, or mismatched CAPTCHA token
            self._handle_captcha_failure(ip_address)
            return False
                
        except Exception as e:
            logger.error(f"Error verifying CAPTCHA for {ip_address}: {e}")
            # On error, require CAPTCHA (fail secure)
            return False
    
    def generate_captcha_token(self, ip_address: str) -> Dict[str, Any]:
        """
        Generate a new CAPTCHA token for an IP address.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Dictionary with CAPTCHA token and challenge data
        """
        try:
            import uuid
            import random
            import string
            
            # Generate unique token
            token = str(uuid.uuid4())
            
            # Generate simple math challenge (for demo purposes)
            # In production, this would integrate with a proper CAPTCHA service
            num1 = random.randint(1, 10)
            num2 = random.randint(1, 10)
            operation = random.choice(['+', '-', '*'])
            
            if operation == '+':
                answer = num1 + num2
            elif operation == '-':
                answer = num1 - num2
            else:  # multiplication
                answer = num1 * num2
            
            challenge = f"{num1} {operation} {num2} = ?"
            
            # Store CAPTCHA data in Redis
            captcha_data = {
                'ip_address': ip_address,
                'answer': answer,
                'challenge': challenge,
                'created_time': datetime.now().timestamp()
            }
            
            captcha_key = f"captcha:{token}"
            self.redis.setex(captcha_key, 300, json.dumps(captcha_data))  # 5 minute expiry
            
            logger.debug(f"Generated CAPTCHA for {ip_address}: {challenge}")
            
            return {
                'token': token,
                'challenge': challenge,
                'expires_in': 300  # seconds
            }
            
        except Exception as e:
            logger.error(f"Error generating CAPTCHA for {ip_address}: {e}")
            return {
                'error': 'Failed to generate CAPTCHA',
                'token': None
            }
    
    def verify_captcha_answer(self, token: str, answer: str, ip_address: str) -> bool:
        """
        Verify CAPTCHA answer and create verification token.
        
        Args:
            token: CAPTCHA token
            answer: User's answer to CAPTCHA challenge
            ip_address: Client IP address
            
        Returns:
            True if answer is correct, False otherwise
        """
        try:
            captcha_key = f"captcha:{token}"
            stored_data = self.redis.get(captcha_key)
            
            if not stored_data:
                logger.warning(f"CAPTCHA token not found or expired: {token}")
                return False
            
            captcha_data = json.loads(stored_data)
            
            # Verify IP matches
            if captcha_data.get('ip_address') != ip_address:
                logger.warning(f"CAPTCHA IP mismatch for token {token}")
                return False
            
            # Verify answer
            correct_answer = captcha_data.get('answer')
            try:
                user_answer = int(answer)
                if user_answer == correct_answer:
                    # Correct answer - create verification token
                    verification_token = str(uuid.uuid4())
                    verification_key = f"captcha:{verification_token}"
                    
                    verification_data = {
                        'ip_address': ip_address,
                        'verified': True,
                        'created_time': datetime.now().timestamp()
                    }
                    
                    # Store verification token (shorter expiry - 2 minutes)
                    self.redis.setex(verification_key, 120, json.dumps(verification_data))
                    
                    # Clean up original challenge
                    self.redis.delete(captcha_key)
                    
                    logger.info(f"CAPTCHA answer correct for {ip_address}")
                    return True
                else:
                    logger.warning(f"CAPTCHA answer incorrect for {ip_address}: {user_answer} != {correct_answer}")
                    
            except ValueError:
                logger.warning(f"Invalid CAPTCHA answer format for {ip_address}: {answer}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying CAPTCHA answer: {e}")
            return False
    
    def _get_session_age(self, request: HttpRequest) -> Optional[int]:
        """
        Get age of current session in seconds.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            Session age in seconds, or None if no session
        """
        try:
            if not request.session.session_key:
                return None
            
            # Try to get session creation time from session data
            session_start = request.session.get('_session_start_time')
            if session_start:
                from django.utils import timezone
                return int((timezone.now().timestamp() - session_start))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session age: {e}")
            return None
    
    def _reduce_threat_score_for_captcha_success(self, ip_address: str) -> None:
        """
        Reduce threat score components for IP after successful CAPTCHA (Requirements 6.4).
        
        Args:
            ip_address: Client IP address
        """
        try:
            # Reduce rate score by resetting the counter partially
            rate_key = f"rate:{ip_address}"
            current_rate = self.redis.get(rate_key)
            if current_rate:
                new_rate = max(0, int(current_rate) - 20)  # Reduce by 20 requests
                if new_rate > 0:
                    self.redis.set(rate_key, new_rate, ex=60)
                else:
                    self.redis.delete(rate_key)
            
            # Clear some pattern history to reduce pattern score
            pattern_key = f"pattern:{ip_address}"
            self.redis.ltrim(pattern_key, 0, 10)  # Keep only last 10 instead of 20
            
            logger.debug(f"Reduced threat factors for {ip_address} after CAPTCHA success")
            
        except Exception as e:
            logger.error(f"Error reducing threat score for {ip_address}: {e}")
    
    def _handle_captcha_failure(self, ip_address: str) -> None:
        """
        Handle CAPTCHA failure by tracking failures and blocking after threshold (Requirements 6.3).
        
        This method implements CAPTCHA failure tracking:
        - Increments failure count in Redis
        - Temporarily blocks IP after 3 failures (Requirements 6.3)
        - Sets 15-minute block duration
        - Logs failure events for monitoring
        
        Args:
            ip_address: Client IP address
        """
        try:
            # Track CAPTCHA failures with sliding window
            failure_key = f"captcha_failures:{ip_address}"
            failures = self.redis.incr(failure_key)
            
            # Set expiry on first failure (15 minutes sliding window)
            if failures == 1:
                self.redis.expire(failure_key, 900)  # 15 minutes
            
            logger.warning(f"CAPTCHA failure #{failures} for {ip_address}")
            
            # Block IP after max failures (Requirements 6.3)
            if failures >= self.captcha_max_failures:
                self._temporary_block_ip(
                    ip_address, 
                    self.captcha_failure_block_duration,  # 15 minutes
                    f"Blocked after {failures} CAPTCHA failures"
                )
                
                # Log security event for CAPTCHA abuse
                try:
                    SecurityLog.objects.create(
                        ip_address=ip_address,
                        threat_score=70,  # High score for CAPTCHA abuse
                        threat_level='HIGH',
                        endpoint='/captcha_failure',
                        method='CAPTCHA',
                        user_agent='CAPTCHA_FAILURE',
                        rate_score=0,
                        pattern_score=0,
                        session_score=0,
                        entropy_score=0,
                        auth_failure_score=0,
                        action_taken='captcha_blocked',
                        blocked_on_blockchain=False
                    )
                except Exception as log_error:
                    logger.error(f"Error logging CAPTCHA failure event: {log_error}")
                
                logger.error(f"IP {ip_address} temporarily blocked due to {failures} CAPTCHA failures")
            
        except Exception as e:
            logger.error(f"Error handling CAPTCHA failure for {ip_address}: {e}")
    
    def _temporary_block_ip(self, ip_address: str, duration_seconds: int, reason: str) -> None:
        """
        Temporarily block IP locally (not on blockchain).
        
        Args:
            ip_address: Client IP address
            duration_seconds: Block duration in seconds
            reason: Reason for blocking
        """
        try:
            # Use Redis for temporary blocks (not blockchain)
            block_key = f"temp_blocked:{ip_address}"
            block_until = datetime.now().timestamp() + duration_seconds
            
            self.redis.setex(block_key, duration_seconds, block_until)
            
            logger.warning(f"Temporarily blocked {ip_address} for {duration_seconds}s: {reason}")
            
        except Exception as e:
            logger.error(f"Error temporarily blocking {ip_address}: {e}")
    
    def _is_temporarily_blocked(self, ip_address: str) -> bool:
        """
        Check if IP is temporarily blocked locally.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            True if temporarily blocked, False otherwise
        """
        try:
            block_key = f"temp_blocked:{ip_address}"
            block_until = self.redis.get(block_key)
            
            if block_until:
                if datetime.now().timestamp() < float(block_until):
                    return True
                else:
                    # Block expired, clean up
                    self.redis.delete(block_key)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking temporary block for {ip_address}: {e}")
            return False
    
    def _create_blocked_response(self, reason: str) -> JsonResponse:
        """
        Create HTTP 403 response for blocked requests.
        
        Args:
            reason: Reason for blocking
            
        Returns:
            JsonResponse with 403 status
        """
        return JsonResponse({
            'error': 'Access denied',
            'reason': reason,
            'status': 'blocked'
        }, status=403)
    
    def _create_captcha_response(self, threat_score: int) -> JsonResponse:
        """
        Create HTTP 429 response requiring CAPTCHA.
        
        Args:
            threat_score: Current threat score
            
        Returns:
            JsonResponse with 429 status and CAPTCHA requirement
        """
        return JsonResponse({
            'error': 'CAPTCHA required',
            'reason': 'Please complete CAPTCHA verification',
            'threat_score': threat_score,
            'status': 'captcha_required',
            'captcha_endpoint': '/api/security/captcha/'
        }, status=429)
    def _log_blockchain_block_event(self, request: HttpRequest, ip_address: str) -> None:
        """
        Log security event when request is blocked due to blockchain blocklist.
        
        Args:
            request: Django HTTP request object
            ip_address: Client IP address
        """
        try:
            SecurityLog.objects.create(
                ip_address=ip_address,
                threat_score=100,  # Max score for blockchain-blocked IPs
                threat_level='HIGH',
                endpoint=request.path,
                method=request.method,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                rate_score=0,
                pattern_score=0,
                session_score=0,
                entropy_score=0,
                auth_failure_score=0,
                action_taken='blockchain_blocked',
                blocked_on_blockchain=True
            )
            
            logger.debug(f"Blockchain block event logged for {ip_address}")
            
        except Exception as e:
            logger.error(f"Error logging blockchain block event: {e}")
    def get_threat_analysis(self, request: HttpRequest, ip_address: str) -> Dict[str, Any]:
        """
        Get detailed threat analysis for debugging and monitoring.
        
        Args:
            request: Django HTTP request object
            ip_address: Client IP address
            
        Returns:
            Dictionary with detailed threat analysis
        """
        try:
            threat_score, factors = self.threat_calculator.calculate_threat_score(request, ip_address)
            threat_level = self.threat_calculator.get_threat_level(threat_score)
            
            # Determine what action would be taken
            if threat_score >= 80:
                action = 'auto_block'
            elif threat_score >= self.thresholds['HIGH']:
                action = 'block'
            elif threat_score >= self.thresholds['MEDIUM']:
                action = 'captcha'
            else:
                action = 'allow'
            
            return {
                'ip_address': ip_address,
                'threat_score': threat_score,
                'threat_level': threat_level,
                'action': action,
                'factors': factors,
                'thresholds': self.thresholds,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting threat analysis: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    def get_security_log_summary(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get summary of security events for monitoring dashboard.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with security log summary
        """
        try:
            from django.utils import timezone
            from django.db.models import Count, Avg
            
            # Calculate time window
            since = timezone.now() - timedelta(hours=hours)
            
            # Get logs in time window
            logs = SecurityLog.objects.filter(timestamp__gte=since)
            
            # Calculate summary statistics
            total_requests = logs.count()
            
            # Group by action taken
            actions = logs.values('action_taken').annotate(count=Count('id'))
            action_summary = {action['action_taken']: action['count'] for action in actions}
            
            # Group by threat level
            levels = logs.values('threat_level').annotate(count=Count('id'))
            level_summary = {level['threat_level']: level['count'] for level in levels}
            
            # Top IPs by request count
            top_ips = logs.values('ip_address').annotate(
                count=Count('id'),
                avg_score=Avg('threat_score')
            ).order_by('-count')[:10]
            
            # Average threat score
            avg_threat_score = logs.aggregate(Avg('threat_score'))['threat_score__avg'] or 0
            
            return {
                'time_window_hours': hours,
                'total_requests': total_requests,
                'average_threat_score': round(avg_threat_score, 2),
                'actions': action_summary,
                'threat_levels': level_summary,
                'top_ips': list(top_ips),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting security log summary: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }