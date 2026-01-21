"""
Anomaly Detection Service for MediChain Healthcare Security System

This module implements pattern analysis across multiple IPs to detect
coordinated attacks and generate attack signatures for blockchain sharing.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from web3 import Web3

logger = logging.getLogger(__name__)


@dataclass
class RequestPattern:
    """Represents a request pattern for analysis"""
    endpoint: str
    method: str
    user_agent: str
    timestamp: datetime
    ip_address: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'endpoint': self.endpoint,
            'method': self.method,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address
        }


@dataclass
class AttackSignature:
    """Represents a detected attack signature"""
    pattern_hash: str
    pattern_data: Dict
    ip_count: int
    request_count: int
    severity: int
    detected_at: datetime
    
    def to_json(self) -> str:
        """Convert to JSON string for blockchain storage"""
        data = {
            'pattern_data': self.pattern_data,
            'ip_count': self.ip_count,
            'request_count': self.request_count,
            'severity': self.severity,
            'detected_at': self.detected_at.isoformat()
        }
        return json.dumps(data, sort_keys=True)


class AnomalyDetector:
    """
    Detects coordinated attacks by analyzing request patterns across multiple IPs.
    
    This class implements Requirements 5.1 and 5.2:
    - Analyzes requests from multiple IPs to identify common behavioral patterns
    - Detects when 50+ IPs show identical patterns within 5 minutes
    - Flags coordinated attacks for signature creation
    """
    
    def __init__(self, redis_client, blockchain_service):
        """
        Initialize the anomaly detector.
        
        Args:
            redis_client: Redis client for pattern tracking
            blockchain_service: Blockchain service for signature storage
        """
        self.redis = redis_client
        self.blockchain = blockchain_service
        
        # Configuration
        self.COORDINATED_ATTACK_THRESHOLD = 50  # Minimum IPs for coordinated attack
        self.PATTERN_WINDOW_MINUTES = 5  # Time window for pattern analysis
        self.PATTERN_SIMILARITY_THRESHOLD = 0.9  # Similarity threshold for identical patterns
        
        # Redis key prefixes
        self.PATTERN_KEY_PREFIX = "anomaly:pattern"
        self.IP_PATTERN_KEY_PREFIX = "anomaly:ip_pattern"
        self.ATTACK_DETECTION_KEY_PREFIX = "anomaly:attack"
    
    def analyze_request_pattern(self, ip_address: str, request) -> Optional[str]:
        """
        Analyze a request and track patterns for anomaly detection.
        
        Args:
            ip_address: Client IP address
            request: Django HTTP request object
            
        Returns:
            Attack signature hash if coordinated attack detected, None otherwise
        """
        try:
            # Create request pattern
            pattern = RequestPattern(
                endpoint=request.path,
                method=request.method,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                timestamp=datetime.now(),
                ip_address=ip_address
            )
            
            # Track pattern for this IP
            self._track_ip_pattern(ip_address, pattern)
            
            # Check for coordinated attacks
            attack_signature = self._detect_coordinated_attack(pattern)
            
            if attack_signature:
                logger.warning(f"Coordinated attack detected: {attack_signature.pattern_hash}")
                return attack_signature.pattern_hash
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing request pattern for {ip_address}: {e}")
            return None
    
    def _track_ip_pattern(self, ip_address: str, pattern: RequestPattern) -> None:
        """
        Track request patterns for a specific IP address.
        
        Args:
            ip_address: Client IP address
            pattern: Request pattern to track
        """
        try:
            # Store pattern for this IP (last 20 requests)
            ip_key = f"{self.IP_PATTERN_KEY_PREFIX}:{ip_address}"
            pattern_json = json.dumps(pattern.to_dict())
            
            # Add to list and trim to last 20
            self.redis.lpush(ip_key, pattern_json)
            self.redis.ltrim(ip_key, 0, 19)
            self.redis.expire(ip_key, self.PATTERN_WINDOW_MINUTES * 60)
            
            # Generate pattern signature for cross-IP analysis
            pattern_signature = self._generate_pattern_signature(pattern)
            
            # Track IPs with this pattern signature
            pattern_key = f"{self.PATTERN_KEY_PREFIX}:{pattern_signature}"
            self.redis.sadd(pattern_key, ip_address)
            self.redis.expire(pattern_key, self.PATTERN_WINDOW_MINUTES * 60)
            
            # Track pattern metadata
            metadata_key = f"{pattern_key}:metadata"
            metadata = {
                'endpoint': pattern.endpoint,
                'method': pattern.method,
                'user_agent_hash': Web3.keccak(text=pattern.user_agent).hex()[:16],
                'first_seen': pattern.timestamp.isoformat()
            }
            
            # Only set if not exists (preserve first_seen)
            if not self.redis.exists(metadata_key):
                self.redis.hmset(metadata_key, metadata)
                self.redis.expire(metadata_key, self.PATTERN_WINDOW_MINUTES * 60)
            
        except Exception as e:
            logger.error(f"Error tracking pattern for {ip_address}: {e}")
    
    def _generate_pattern_signature(self, pattern: RequestPattern) -> str:
        """
        Generate a signature hash for a request pattern.
        
        Args:
            pattern: Request pattern
            
        Returns:
            Pattern signature hash
        """
        # Create signature from key pattern characteristics
        signature_data = {
            'endpoint': pattern.endpoint,
            'method': pattern.method,
            'user_agent_hash': Web3.keccak(text=pattern.user_agent).hex()[:16]
        }
        
        signature_string = json.dumps(signature_data, sort_keys=True)
        return Web3.keccak(text=signature_string).hex()
    
    def _detect_coordinated_attack(self, current_pattern: RequestPattern) -> Optional[AttackSignature]:
        """
        Detect coordinated attacks by analyzing pattern distribution across IPs.
        
        Args:
            current_pattern: Current request pattern
            
        Returns:
            AttackSignature if coordinated attack detected, None otherwise
        """
        try:
            pattern_signature = self._generate_pattern_signature(current_pattern)
            pattern_key = f"{self.PATTERN_KEY_PREFIX}:{pattern_signature}"
            
            # Get IPs with this pattern
            ips_with_pattern = self.redis.smembers(pattern_key)
            ip_count = len(ips_with_pattern)
            
            logger.debug(f"Pattern {pattern_signature[:16]}... seen from {ip_count} IPs")
            
            # Check if we've reached the coordinated attack threshold
            if ip_count >= self.COORDINATED_ATTACK_THRESHOLD:
                # Check if we've already detected this attack
                attack_key = f"{self.ATTACK_DETECTION_KEY_PREFIX}:{pattern_signature}"
                if self.redis.exists(attack_key):
                    logger.debug(f"Attack already detected for pattern {pattern_signature[:16]}...")
                    return None
                
                # Mark attack as detected (prevent duplicate detection)
                self.redis.setex(attack_key, self.PATTERN_WINDOW_MINUTES * 60, "detected")
                
                # Calculate request count across all IPs
                total_requests = self._calculate_total_requests(ips_with_pattern, pattern_signature)
                
                # Calculate severity based on IP count and request volume
                severity = self._calculate_attack_severity(ip_count, total_requests)
                
                # Get pattern metadata
                metadata_key = f"{pattern_key}:metadata"
                metadata = self.redis.hgetall(metadata_key)
                
                # Create attack signature
                pattern_data = {
                    'endpoint': metadata.get('endpoint', current_pattern.endpoint),
                    'method': metadata.get('method', current_pattern.method),
                    'user_agent_hash': metadata.get('user_agent_hash', ''),
                    'detection_threshold': self.COORDINATED_ATTACK_THRESHOLD,
                    'time_window_minutes': self.PATTERN_WINDOW_MINUTES
                }
                
                attack_signature = AttackSignature(
                    pattern_hash=pattern_signature,
                    pattern_data=pattern_data,
                    ip_count=ip_count,
                    request_count=total_requests,
                    severity=severity,
                    detected_at=datetime.now()
                )
                
                logger.warning(
                    f"Coordinated attack detected: {ip_count} IPs, "
                    f"{total_requests} requests, severity {severity}"
                )
                
                # Store attack signature on blockchain and local database
                self._store_attack_signature(attack_signature)
                
                return attack_signature
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting coordinated attack: {e}")
            return None
    
    def _calculate_total_requests(self, ips_with_pattern: Set[str], pattern_signature: str) -> int:
        """
        Calculate total request count for a pattern across all IPs.
        
        Args:
            ips_with_pattern: Set of IP addresses with the pattern
            pattern_signature: Pattern signature hash
            
        Returns:
            Total request count
        """
        total_requests = 0
        
        try:
            for ip in ips_with_pattern:
                ip_key = f"{self.IP_PATTERN_KEY_PREFIX}:{ip}"
                patterns = self.redis.lrange(ip_key, 0, -1)
                
                # Count requests matching this pattern signature
                for pattern_json in patterns:
                    try:
                        pattern_data = json.loads(pattern_json)
                        pattern_obj = RequestPattern(
                            endpoint=pattern_data['endpoint'],
                            method=pattern_data['method'],
                            user_agent=pattern_data['user_agent'],
                            timestamp=datetime.fromisoformat(pattern_data['timestamp']),
                            ip_address=pattern_data['ip_address']
                        )
                        
                        if self._generate_pattern_signature(pattern_obj) == pattern_signature:
                            total_requests += 1
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Invalid pattern data in Redis: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error calculating total requests: {e}")
            
        return total_requests
    
    def _calculate_attack_severity(self, ip_count: int, request_count: int) -> int:
        """
        Calculate attack severity based on IP count and request volume.
        
        Args:
            ip_count: Number of IPs involved
            request_count: Total request count
            
        Returns:
            Severity level (1-10)
        """
        # Base severity on IP count
        if ip_count >= 200:
            base_severity = 10
        elif ip_count >= 150:
            base_severity = 9
        elif ip_count >= 100:
            base_severity = 8
        elif ip_count >= 75:
            base_severity = 7
        else:
            base_severity = 6  # Minimum for coordinated attack
        
        # Adjust based on request volume
        requests_per_ip = request_count / ip_count if ip_count > 0 else 0
        
        if requests_per_ip >= 20:
            base_severity = min(10, base_severity + 2)
        elif requests_per_ip >= 10:
            base_severity = min(10, base_severity + 1)
        
        return base_severity
    
    def _store_attack_signature(self, attack_signature: AttackSignature) -> bool:
        """
        Store attack signature on blockchain and in local database.
        
        Args:
            attack_signature: Attack signature to store
            
        Returns:
            True if successfully stored, False otherwise
        """
        try:
            # Store on blockchain (Requirements 5.3, 5.4)
            pattern_json = attack_signature.to_json()
            tx_hash, success = self.blockchain.add_attack_signature(
                pattern_json, 
                attack_signature.severity
            )
            
            if success:
                logger.info(f"Attack signature stored on blockchain: {tx_hash}")
                
                # Store in local database
                self._save_attack_pattern_to_db(attack_signature, tx_hash)
                
                return True
            else:
                logger.error(f"Failed to store attack signature on blockchain")
                
                # Still save to local database for retry later
                self._save_attack_pattern_to_db(attack_signature, None)
                
                return False
                
        except Exception as e:
            logger.error(f"Error storing attack signature: {e}")
            
            # Try to save to local database at least
            try:
                self._save_attack_pattern_to_db(attack_signature, None)
            except Exception as db_error:
                logger.error(f"Failed to save attack pattern to database: {db_error}")
            
            return False
    
    def _save_attack_pattern_to_db(self, attack_signature: AttackSignature, tx_hash: Optional[str]) -> None:
        """
        Save attack pattern to local database.
        
        Args:
            attack_signature: Attack signature to save
            tx_hash: Blockchain transaction hash (if available)
        """
        try:
            from firewall.models import AttackPattern
            
            # Check if pattern already exists
            existing_pattern = AttackPattern.objects.filter(
                pattern_hash=attack_signature.pattern_hash
            ).first()
            
            if existing_pattern:
                logger.debug(f"Attack pattern already exists: {attack_signature.pattern_hash}")
                
                # Update blockchain sync status if we have a new tx_hash
                if tx_hash and not existing_pattern.blockchain_synced:
                    existing_pattern.signature_tx_hash = tx_hash
                    existing_pattern.blockchain_synced = True
                    existing_pattern.save()
                    logger.info(f"Updated blockchain sync status for pattern {attack_signature.pattern_hash}")
                
                return
            
            # Create new attack pattern record
            attack_pattern = AttackPattern.objects.create(
                pattern_hash=attack_signature.pattern_hash,
                pattern_data=attack_signature.pattern_data,
                detected_at=attack_signature.detected_at,
                severity=attack_signature.severity,
                ip_count=attack_signature.ip_count,
                request_count=attack_signature.request_count,
                blockchain_synced=bool(tx_hash),
                signature_tx_hash=tx_hash or ''
            )
            
            logger.info(f"Attack pattern saved to database: {attack_pattern.id}")
            
        except Exception as e:
            logger.error(f"Error saving attack pattern to database: {e}")
            raise
    
    def get_attack_signature_by_hash(self, pattern_hash: str) -> Optional[AttackSignature]:
        """
        Retrieve attack signature by hash from local database.
        
        Args:
            pattern_hash: Pattern hash to look up
            
        Returns:
            AttackSignature if found, None otherwise
        """
        try:
            from firewall.models import AttackPattern
            
            pattern = AttackPattern.objects.filter(pattern_hash=pattern_hash).first()
            if not pattern:
                return None
            
            return AttackSignature(
                pattern_hash=pattern.pattern_hash,
                pattern_data=pattern.pattern_data,
                ip_count=pattern.ip_count,
                request_count=pattern.request_count,
                severity=pattern.severity,
                detected_at=pattern.detected_at
            )
            
        except Exception as e:
            logger.error(f"Error retrieving attack signature {pattern_hash}: {e}")
            return None
    
    def sync_pending_signatures(self) -> int:
        """
        Sync attack signatures that failed to upload to blockchain.
        
        Returns:
            Number of signatures successfully synced
        """
        try:
            from firewall.models import AttackPattern
            
            # Get patterns that haven't been synced to blockchain
            pending_patterns = AttackPattern.objects.filter(blockchain_synced=False)
            synced_count = 0
            
            for pattern in pending_patterns:
                try:
                    # Recreate attack signature object
                    attack_signature = AttackSignature(
                        pattern_hash=pattern.pattern_hash,
                        pattern_data=pattern.pattern_data,
                        ip_count=pattern.ip_count,
                        request_count=pattern.request_count,
                        severity=pattern.severity,
                        detected_at=pattern.detected_at
                    )
                    
                    # Try to store on blockchain
                    pattern_json = attack_signature.to_json()
                    tx_hash, success = self.blockchain.add_attack_signature(
                        pattern_json, 
                        attack_signature.severity
                    )
                    
                    if success:
                        # Update database record
                        pattern.signature_tx_hash = tx_hash
                        pattern.blockchain_synced = True
                        pattern.save()
                        
                        synced_count += 1
                        logger.info(f"Synced attack pattern {pattern.pattern_hash} to blockchain")
                    
                except Exception as e:
                    logger.error(f"Failed to sync pattern {pattern.pattern_hash}: {e}")
                    continue
            
            if synced_count > 0:
                logger.info(f"Successfully synced {synced_count} attack patterns to blockchain")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing pending signatures: {e}")
            return 0
    
    def get_recent_patterns(self, minutes: int = 5) -> Dict[str, Dict]:
        """
        Get recent attack patterns for analysis.
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            Dictionary of pattern signatures and their metadata
        """
        try:
            patterns = {}
            
            # Get all pattern keys
            pattern_keys = self.redis.keys(f"{self.PATTERN_KEY_PREFIX}:*")
            
            for key in pattern_keys:
                if key.endswith(':metadata'):
                    continue
                    
                pattern_signature = key.split(':')[-1]
                
                # Get IPs with this pattern
                ips = self.redis.smembers(key)
                
                # Get metadata
                metadata_key = f"{key}:metadata"
                metadata = self.redis.hgetall(metadata_key)
                
                if ips and metadata:
                    patterns[pattern_signature] = {
                        'ip_count': len(ips),
                        'ips': list(ips),
                        'metadata': metadata
                    }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error getting recent patterns: {e}")
            return {}
    
    def cleanup_expired_patterns(self) -> int:
        """
        Clean up expired pattern data from Redis.
        
        Returns:
            Number of patterns cleaned up
        """
        try:
            cleaned_count = 0
            
            # Get all pattern keys
            pattern_keys = self.redis.keys(f"{self.PATTERN_KEY_PREFIX}:*")
            ip_pattern_keys = self.redis.keys(f"{self.IP_PATTERN_KEY_PREFIX}:*")
            attack_keys = self.redis.keys(f"{self.ATTACK_DETECTION_KEY_PREFIX}:*")
            
            # Redis TTL handles most cleanup, but we can manually clean up empty sets
            for key in pattern_keys:
                if not key.endswith(':metadata'):
                    if self.redis.scard(key) == 0:
                        self.redis.delete(key)
                        # Also delete associated metadata
                        metadata_key = f"{key}:metadata"
                        self.redis.delete(metadata_key)
                        cleaned_count += 1
            
            logger.debug(f"Cleaned up {cleaned_count} expired patterns")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired patterns: {e}")
            return 0