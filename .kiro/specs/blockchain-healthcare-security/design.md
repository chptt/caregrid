# Design Document

## Overview

MediChain is a blockchain-integrated healthcare security system that combines Django REST API backend with Ethereum smart contracts to provide universal patient identification and advanced DDoS attack detection. The system uses a multi-factor threat scoring algorithm to detect sophisticated distributed attacks that traditional IP-based rate limiting cannot catch. All security intelligence and patient identifiers are stored on a local Hardhat blockchain network, making the system fully functional offline for development and demonstration purposes.

The architecture follows a three-tier design: (1) Django REST API layer handling HTTP requests and business logic, (2) Redis caching layer for high-performance rate limiting and request tracking, and (3) Blockchain layer (Hardhat local network) for immutable patient IDs and distributed IP blocklist. This design allows the system to run completely offline while demonstrating real blockchain integration.

## Architecture

### System Components

**1. Django Backend (Python)**
- REST API endpoints for patient management, appointments, and security monitoring
- Middleware for request interception and threat analysis
- Web3.py integration for blockchain communication
- Django ORM for local database operations
- Celery for background tasks (optional for advanced features)

**2. Blockchain Layer (Hardhat + Solidity)**
- Local Ethereum network running on localhost:8545
- PatientRegistry smart contract for universal patient IDs
- BlockedIPRegistry smart contract (enhance existing)
- AttackSignatureRegistry for sharing attack patterns
- No internet required - fully local development

**3. Caching Layer (Redis)**
- Request rate tracking per IP
- Threat score caching
- Session management
- Distributed rate limiting

**4. Security Monitor (Python)**
- Multi-factor threat scoring engine
- Pattern recognition algorithms
- Anomaly detection
- CAPTCHA integration

### Component Interaction Flow

```
HTTP Request
    ↓
Django Middleware (IP Extraction)
    ↓
Security Monitor (Threat Scoring)
    ↓
Redis (Rate Limit Check)
    ↓
Blockchain (IP Blocklist Check) ← Web3.py
    ↓
[High Threat] → Block & Log to Blockchain
[Medium Threat] → CAPTCHA Challenge
[Low Threat] → Process Normally
    ↓
Django View (Business Logic)
    ↓
Response
```


## Components and Interfaces

### 1. Smart Contracts (Solidity)

#### PatientRegistry Contract

```solidity
contract PatientRegistry {
    struct Patient {
        bytes32 patientIdHash;      // Hashed patient ID for privacy
        uint256 registrationTime;
        address registeredBy;       // Hospital/branch that registered
        bool isActive;
    }
    
    mapping(bytes32 => Patient) public patients;
    mapping(bytes32 => bool) public patientExists;
    
    event PatientRegistered(bytes32 indexed patientIdHash, uint256 timestamp);
    event PatientDeactivated(bytes32 indexed patientIdHash);
    
    function registerPatient(bytes32 patientIdHash) external returns (bool);
    function isPatientRegistered(bytes32 patientIdHash) external view returns (bool);
    function getPatient(bytes32 patientIdHash) external view returns (Patient memory);
}
```

#### Enhanced BlockedIPRegistry Contract

```solidity
contract BlockedIPRegistry {
    struct BlockEntry {
        bytes32 ipHash;             // Hashed IP for privacy
        uint256 blockTime;
        uint256 expiryTime;         // Auto-unblock time
        string reason;
        address blockedBy;
        bool isManual;              // Manual vs automatic block
    }
    
    mapping(bytes32 => BlockEntry) public blockedIPs;
    mapping(bytes32 => bool) public isBlocked;
    bytes32[] public blockedIPList;
    
    event IPBlocked(bytes32 indexed ipHash, uint256 expiryTime, string reason);
    event IPUnblocked(bytes32 indexed ipHash);
    
    function blockIP(bytes32 ipHash, uint256 duration, string memory reason) external;
    function unblockIP(bytes32 ipHash) external;
    function isIPBlocked(bytes32 ipHash) external view returns (bool);
    function cleanupExpiredBlocks() external;
}
```

#### AttackSignatureRegistry Contract

```solidity
contract AttackSignatureRegistry {
    struct AttackSignature {
        bytes32 signatureHash;
        string pattern;             // JSON string describing attack pattern
        uint256 detectedTime;
        address reportedBy;
        uint256 severity;           // 1-10 scale
    }
    
    mapping(bytes32 => AttackSignature) public signatures;
    bytes32[] public signatureList;
    
    event AttackSignatureAdded(bytes32 indexed signatureHash, uint256 severity);
    
    function addSignature(string memory pattern, uint256 severity) external;
    function getSignature(bytes32 signatureHash) external view returns (AttackSignature memory);
    function getAllSignatures() external view returns (bytes32[] memory);
}
```


### 2. Django Models

#### Enhanced Patient Model

```python
from django.db import models
from web3 import Web3

class Patient(models.Model):
    # Local database fields
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    address = models.TextField()
    
    # Blockchain integration
    blockchain_id = models.CharField(max_length=66, unique=True)  # bytes32 hex
    blockchain_registered = models.BooleanField(default=False)
    registration_tx_hash = models.CharField(max_length=66, blank=True)
    
    # Multi-branch support
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def generate_blockchain_id(self):
        """Generate unique blockchain ID from patient data"""
        data = f"{self.name}{self.date_of_birth}{self.contact_email}"
        return Web3.keccak(text=data).hex()
    
    def register_on_blockchain(self):
        """Register patient ID on blockchain"""
        # Implementation in blockchain service
        pass
```

#### SecurityLog Model

```python
class SecurityLog(models.Model):
    THREAT_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    ip_address = models.GenericIPAddressField()
    threat_score = models.IntegerField()
    threat_level = models.CharField(max_length=10, choices=THREAT_LEVEL_CHOICES)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Threat factors
    rate_score = models.IntegerField(default=0)
    pattern_score = models.IntegerField(default=0)
    session_score = models.IntegerField(default=0)
    entropy_score = models.IntegerField(default=0)
    auth_failure_score = models.IntegerField(default=0)
    
    # Action taken
    action_taken = models.CharField(max_length=50)  # 'allowed', 'captcha', 'blocked'
    blocked_on_blockchain = models.BooleanField(default=False)
    block_tx_hash = models.CharField(max_length=66, blank=True)
```

#### BlockedIP Model

```python
class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    ip_hash = models.CharField(max_length=66)  # Blockchain hash
    block_time = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()
    reason = models.TextField()
    is_manual = models.BooleanField(default=False)
    blocked_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    blockchain_synced = models.BooleanField(default=False)
    block_tx_hash = models.CharField(max_length=66, blank=True)
```

#### AttackPattern Model

```python
class AttackPattern(models.Model):
    pattern_hash = models.CharField(max_length=66, unique=True)
    pattern_data = models.JSONField()  # Store pattern characteristics
    detected_at = models.DateTimeField(auto_now_add=True)
    severity = models.IntegerField()  # 1-10
    ip_count = models.IntegerField()  # Number of IPs involved
    request_count = models.IntegerField()
    blockchain_synced = models.BooleanField(default=False)
    signature_tx_hash = models.CharField(max_length=66, blank=True)
```


### 3. Security Monitor Service

#### ThreatScoreCalculator Class

```python
class ThreatScoreCalculator:
    """
    Multi-factor threat scoring engine that analyzes request patterns
    to detect DDoS attacks beyond simple IP rate limiting.
    """
    
    def __init__(self, redis_client, blockchain_service):
        self.redis = redis_client
        self.blockchain = blockchain_service
        
    def calculate_threat_score(self, request, ip_address):
        """
        Calculate comprehensive threat score (0-100) based on multiple factors.
        Returns: (score, factor_breakdown)
        """
        factors = {}
        
        # Factor 1: Request rate (0-20 points)
        factors['rate'] = self._calculate_rate_score(ip_address)
        
        # Factor 2: Pattern repetition (0-25 points)
        factors['pattern'] = self._calculate_pattern_score(ip_address, request)
        
        # Factor 3: Session behavior (0-20 points)
        factors['session'] = self._calculate_session_score(request)
        
        # Factor 4: User-Agent entropy (0-15 points)
        factors['entropy'] = self._calculate_entropy_score(ip_address)
        
        # Factor 5: Authentication failures (0-10 points)
        factors['auth_failures'] = self._calculate_auth_failure_score(ip_address)
        
        # Factor 6: Known attack signature match (0-30 points)
        factors['signature_match'] = self._check_attack_signatures(ip_address, request)
        
        total_score = sum(factors.values())
        return min(total_score, 100), factors
    
    def _calculate_rate_score(self, ip_address):
        """Score based on requests per minute"""
        key = f"rate:{ip_address}"
        count = self.redis.incr(key)
        self.redis.expire(key, 60)  # 1 minute window
        
        if count > 100:
            return 20
        elif count > 50:
            return 15
        elif count > 30:
            return 10
        return 0
    
    def _calculate_pattern_score(self, ip_address, request):
        """Score based on endpoint repetition"""
        key = f"pattern:{ip_address}"
        endpoint = request.path
        
        # Track last 20 requests
        self.redis.lpush(key, endpoint)
        self.redis.ltrim(key, 0, 19)
        self.redis.expire(key, 300)  # 5 minutes
        
        requests = self.redis.lrange(key, 0, -1)
        if len(requests) < 10:
            return 0
        
        # Calculate endpoint diversity
        unique_endpoints = len(set(requests))
        repetition_ratio = 1 - (unique_endpoints / len(requests))
        
        if repetition_ratio > 0.8:  # 80% same endpoint
            return 25
        elif repetition_ratio > 0.6:
            return 15
        elif repetition_ratio > 0.4:
            return 5
        return 0
    
    def _calculate_session_score(self, request):
        """Score based on session/cookie presence"""
        has_session = bool(request.session.session_key)
        has_cookies = bool(request.COOKIES)
        is_authenticated = request.user.is_authenticated
        
        if is_authenticated:
            return 0  # Authenticated users get no penalty
        if not has_session and not has_cookies:
            return 20  # No session = likely bot
        if not has_session:
            return 10
        return 0
    
    def _calculate_entropy_score(self, ip_address):
        """Score based on User-Agent variety"""
        key = f"ua:{ip_address}"
        user_agents = self.redis.smembers(key)
        
        if len(user_agents) == 0:
            return 0
        elif len(user_agents) == 1:
            return 15  # Always same UA = bot
        elif len(user_agents) > 5:
            return 10  # Too many different UAs = suspicious
        return 0
    
    def _calculate_auth_failure_score(self, ip_address):
        """Score based on failed login attempts"""
        key = f"auth_fail:{ip_address}"
        failures = self.redis.get(key)
        
        if failures is None:
            return 0
        
        failures = int(failures)
        if failures > 10:
            return 10
        elif failures > 5:
            return 7
        elif failures > 3:
            return 3
        return 0
    
    def _check_attack_signatures(self, ip_address, request):
        """Check if request matches known attack patterns"""
        # Get attack signatures from blockchain
        signatures = self.blockchain.get_attack_signatures()
        
        for sig in signatures:
            if self._matches_signature(ip_address, request, sig):
                return 30  # Strong indicator of attack
        
        return 0
    
    def _matches_signature(self, ip_address, request, signature):
        """Check if current request matches attack signature"""
        # Implementation depends on signature format
        # Example: check if endpoint, method, and rate match signature
        return False  # Placeholder
```


### 4. Blockchain Service

#### BlockchainService Class

```python
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json

class BlockchainService:
    """
    Service for interacting with Hardhat local blockchain.
    Handles patient registration and IP blocking on-chain.
    """
    
    def __init__(self):
        # Connect to local Hardhat network
        self.w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Load contract ABIs and addresses
        self.patient_registry = self._load_contract('PatientRegistry')
        self.blocked_ip_registry = self._load_contract('BlockedIPRegistry')
        self.attack_signature_registry = self._load_contract('AttackSignatureRegistry')
        
        # Use first account from Hardhat for transactions
        self.account = self.w3.eth.accounts[0]
    
    def _load_contract(self, contract_name):
        """Load contract ABI and create contract instance"""
        with open(f'caregrid_chain/artifacts/contracts/{contract_name}.sol/{contract_name}.json') as f:
            contract_json = json.load(f)
        
        # Load deployed address from deployment file
        with open(f'caregrid_chain/deployments/{contract_name}.json') as f:
            deployment = json.load(f)
        
        return self.w3.eth.contract(
            address=deployment['address'],
            abi=contract_json['abi']
        )
    
    def register_patient(self, patient_id_hash):
        """Register patient ID on blockchain"""
        try:
            tx_hash = self.patient_registry.functions.registerPatient(
                patient_id_hash
            ).transact({'from': self.account})
            
            # Wait for transaction confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt.transactionHash.hex(), receipt.status == 1
        except Exception as e:
            print(f"Blockchain registration error: {e}")
            return None, False
    
    def is_patient_registered(self, patient_id_hash):
        """Check if patient is registered on blockchain"""
        try:
            return self.patient_registry.functions.isPatientRegistered(
                patient_id_hash
            ).call()
        except Exception as e:
            print(f"Blockchain query error: {e}")
            return False
    
    def block_ip(self, ip_hash, duration_seconds, reason):
        """Add IP to blockchain blocklist"""
        try:
            expiry_time = self.w3.eth.get_block('latest')['timestamp'] + duration_seconds
            
            tx_hash = self.blocked_ip_registry.functions.blockIP(
                ip_hash,
                expiry_time,
                reason
            ).transact({'from': self.account})
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt.transactionHash.hex(), receipt.status == 1
        except Exception as e:
            print(f"Blockchain block error: {e}")
            return None, False
    
    def is_ip_blocked(self, ip_hash):
        """Check if IP is blocked on blockchain"""
        try:
            return self.blocked_ip_registry.functions.isIPBlocked(
                ip_hash
            ).call()
        except Exception as e:
            print(f"Blockchain query error: {e}")
            return False
    
    def unblock_ip(self, ip_hash):
        """Remove IP from blockchain blocklist"""
        try:
            tx_hash = self.blocked_ip_registry.functions.unblockIP(
                ip_hash
            ).transact({'from': self.account})
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt.transactionHash.hex(), receipt.status == 1
        except Exception as e:
            print(f"Blockchain unblock error: {e}")
            return None, False
    
    def add_attack_signature(self, pattern_json, severity):
        """Add attack signature to blockchain"""
        try:
            tx_hash = self.attack_signature_registry.functions.addSignature(
                pattern_json,
                severity
            ).transact({'from': self.account})
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt.transactionHash.hex(), receipt.status == 1
        except Exception as e:
            print(f"Blockchain signature error: {e}")
            return None, False
    
    def get_attack_signatures(self):
        """Retrieve all attack signatures from blockchain"""
        try:
            signature_hashes = self.attack_signature_registry.functions.getAllSignatures().call()
            signatures = []
            
            for sig_hash in signature_hashes:
                sig = self.attack_signature_registry.functions.getSignature(sig_hash).call()
                signatures.append({
                    'hash': sig_hash.hex(),
                    'pattern': json.loads(sig[1]),  # Parse JSON pattern
                    'severity': sig[4]
                })
            
            return signatures
        except Exception as e:
            print(f"Blockchain query error: {e}")
            return []
```


### 5. Django Middleware

#### SecurityMiddleware Class

```python
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from web3 import Web3

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware that intercepts all requests and performs threat analysis.
    Blocks high-threat requests and challenges medium-threat requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        from .services import ThreatScoreCalculator, BlockchainService
        import redis
        
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.blockchain = BlockchainService()
        self.threat_calculator = ThreatScoreCalculator(self.redis, self.blockchain)
    
    def process_request(self, request):
        # Skip security check for admin and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
        
        # Extract IP address
        ip_address = self._get_client_ip(request)
        ip_hash = Web3.keccak(text=ip_address)
        
        # Check blockchain blocklist first
        if self.blockchain.is_ip_blocked(ip_hash):
            return JsonResponse({
                'error': 'Access denied',
                'reason': 'IP blocked due to security policy'
            }, status=403)
        
        # Calculate threat score
        threat_score, factors = self.threat_calculator.calculate_threat_score(request, ip_address)
        
        # Log security event
        self._log_security_event(request, ip_address, threat_score, factors)
        
        # Take action based on threat level
        if threat_score >= 80:
            # High threat - auto-block
            self._auto_block_ip(ip_address, ip_hash, threat_score)
            return JsonResponse({
                'error': 'Access denied',
                'reason': 'Suspicious activity detected'
            }, status=403)
        
        elif threat_score >= 60:
            # High threat - block but don't auto-add to blockchain
            return JsonResponse({
                'error': 'Access denied',
                'reason': 'Multiple security violations detected'
            }, status=403)
        
        elif threat_score >= 40:
            # Medium threat - require CAPTCHA
            if not self._verify_captcha(request):
                return JsonResponse({
                    'error': 'CAPTCHA required',
                    'reason': 'Please complete CAPTCHA verification',
                    'threat_score': threat_score
                }, status=429)
        
        # Low threat or CAPTCHA passed - allow request
        request.threat_score = threat_score
        request.threat_factors = factors
        return None
    
    def _get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _log_security_event(self, request, ip_address, threat_score, factors):
        """Log security event to database"""
        from firewall.models import SecurityLog
        
        threat_level = 'HIGH' if threat_score >= 60 else 'MEDIUM' if threat_score >= 40 else 'LOW'
        
        SecurityLog.objects.create(
            ip_address=ip_address,
            threat_score=threat_score,
            threat_level=threat_level,
            endpoint=request.path,
            method=request.method,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            rate_score=factors.get('rate', 0),
            pattern_score=factors.get('pattern', 0),
            session_score=factors.get('session', 0),
            entropy_score=factors.get('entropy', 0),
            auth_failure_score=factors.get('auth_failures', 0),
            action_taken='blocked' if threat_score >= 60 else 'captcha' if threat_score >= 40 else 'allowed'
        )
    
    def _auto_block_ip(self, ip_address, ip_hash, threat_score):
        """Automatically block IP on blockchain"""
        from firewall.models import BlockedIP
        from datetime import datetime, timedelta
        
        # Block for 24 hours
        expiry = datetime.now() + timedelta(hours=24)
        
        # Add to blockchain
        tx_hash, success = self.blockchain.block_ip(
            ip_hash,
            86400,  # 24 hours in seconds
            f"Auto-blocked: threat score {threat_score}"
        )
        
        # Add to local database
        BlockedIP.objects.create(
            ip_address=ip_address,
            ip_hash=ip_hash.hex(),
            expiry_time=expiry,
            reason=f"Automatic block - threat score: {threat_score}",
            is_manual=False,
            blockchain_synced=success,
            block_tx_hash=tx_hash or ''
        )
    
    def _verify_captcha(self, request):
        """Verify CAPTCHA response"""
        # Check if CAPTCHA token is present and valid
        captcha_token = request.META.get('HTTP_X_CAPTCHA_TOKEN')
        if not captcha_token:
            return False
        
        # Verify token (implementation depends on CAPTCHA service)
        # For now, just check if token exists in Redis
        key = f"captcha:{captcha_token}"
        if self.redis.exists(key):
            self.redis.delete(key)
            return True
        
        return False
```


## Data Models

### Patient Data Flow

```
User Registration Request
    ↓
Django View validates data
    ↓
Generate blockchain_id = keccak256(name + dob + email)
    ↓
Save to local database (Patient model)
    ↓
Call blockchain.register_patient(blockchain_id)
    ↓
Wait for transaction confirmation
    ↓
Update Patient.blockchain_registered = True
    ↓
Return success response with universal patient ID
```

### Security Event Data Flow

```
HTTP Request arrives
    ↓
SecurityMiddleware intercepts
    ↓
Calculate threat score (multi-factor)
    ↓
Log to SecurityLog model
    ↓
[If high threat]
    ↓
    Create BlockedIP record
    ↓
    Call blockchain.block_ip()
    ↓
    Update BlockedIP.blockchain_synced
    ↓
    Return 403 response
```

### Database Schema

**patients table:**
- id (PK)
- name
- date_of_birth
- gender
- contact_phone
- contact_email
- address
- blockchain_id (unique, indexed)
- blockchain_registered (boolean)
- registration_tx_hash
- branch_id (FK)
- created_at
- updated_at

**security_logs table:**
- id (PK)
- ip_address (indexed)
- threat_score
- threat_level
- endpoint
- method
- user_agent
- rate_score
- pattern_score
- session_score
- entropy_score
- auth_failure_score
- action_taken
- blocked_on_blockchain
- block_tx_hash
- timestamp (indexed)

**blocked_ips table:**
- id (PK)
- ip_address (unique, indexed)
- ip_hash
- block_time
- expiry_time (indexed)
- reason
- is_manual
- blocked_by_id (FK, nullable)
- blockchain_synced
- block_tx_hash

**attack_patterns table:**
- id (PK)
- pattern_hash (unique)
- pattern_data (JSON)
- detected_at
- severity
- ip_count
- request_count
- blockchain_synced
- signature_tx_hash

### Redis Data Structures

**Rate limiting:**
- Key: `rate:{ip_address}`
- Type: Integer (counter)
- TTL: 60 seconds
- Value: Request count in current minute

**Pattern tracking:**
- Key: `pattern:{ip_address}`
- Type: List
- TTL: 300 seconds
- Value: Last 20 endpoints accessed

**User-Agent tracking:**
- Key: `ua:{ip_address}`
- Type: Set
- TTL: 3600 seconds
- Value: Unique User-Agent strings

**Auth failure tracking:**
- Key: `auth_fail:{ip_address}`
- Type: Integer (counter)
- TTL: 600 seconds
- Value: Failed login attempts

**CAPTCHA tokens:**
- Key: `captcha:{token}`
- Type: String
- TTL: 300 seconds
- Value: IP address that generated token


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Patient ID Properties

**Property 1: Patient ID Uniqueness**
*For any* two different patients with different registration data, the generated blockchain IDs must be unique.
**Validates: Requirements 1.1, 1.4**

**Property 2: Patient ID Determinism**
*For any* patient data, generating the blockchain ID multiple times with the same input must produce the same ID.
**Validates: Requirements 1.1**

**Property 3: Blockchain Registration Persistence**
*For any* patient that is successfully registered, querying the blockchain with their ID hash must return true for isPatientRegistered.
**Validates: Requirements 1.2**

**Property 4: Cross-Branch Patient Retrieval**
*For any* patient registered at one branch, querying from any other branch using the universal patient ID must retrieve the same patient information.
**Validates: Requirements 1.3, 8.4**

**Property 5: Privacy Preservation**
*For any* patient registered on blockchain, the on-chain data must contain only the hashed ID, not any personally identifiable information.
**Validates: Requirements 1.5**

### Threat Scoring Properties

**Property 6: Multi-Factor Scoring**
*For any* request, the threat score calculation must include at least 5 distinct behavioral factors (rate, pattern, session, entropy, auth failures).
**Validates: Requirements 2.1**

**Property 7: Rate Score Calculation**
*For any* IP address with request rate exceeding 100 per minute, the rate score component must be 20 points.
**Validates: Requirements 2.2**

**Property 8: Pattern Score Calculation**
*For any* IP address with more than 80% requests to the same endpoint, the pattern score component must be 25 points.
**Validates: Requirements 2.3**

**Property 9: Session Score Calculation**
*For any* request without session cookies or authentication, the session score component must be 20 points.
**Validates: Requirements 2.4**

**Property 10: Threat Classification Boundaries**
*For any* request with threat score >= 60, it must be classified as high threat; score 40-59 as medium threat; score < 40 as low threat.
**Validates: Requirements 2.7, 2.8, 2.9**

**Property 11: Score Monotonicity**
*For any* request, adding more suspicious factors must never decrease the total threat score.
**Validates: Requirements 2.1**

### Security Logging Properties

**Property 12: Complete Log Entries**
*For any* request processed by the security middleware, the log entry must contain IP address, timestamp, endpoint, and User-Agent.
**Validates: Requirements 3.1**

**Property 13: Log Temporal Ordering**
*For any* sequence of logged requests, they must be ordered by timestamp in ascending order.
**Validates: Requirements 3.2**

**Property 14: Rate Tracking Accuracy**
*For any* IP address, the tracked request count per minute must equal the actual number of requests received from that IP in the time window.
**Validates: Requirements 3.3**

### Blockchain Blocklist Properties

**Property 15: Blocked IP Rejection**
*For any* IP address that exists in the blockchain blocklist, requests from that IP must be rejected with HTTP 403 status.
**Validates: Requirements 4.3, 4.4**

**Property 16: Blocklist Entry Completeness**
*For any* IP added to the blocklist, the blockchain entry must contain the IP hash, timestamp, and reason.
**Validates: Requirements 4.2**

**Property 17: Blocklist Synchronization**
*For any* IP blocked at one branch, querying the blockchain from any other branch must show that IP as blocked.
**Validates: Requirements 4.1**

**Property 18: Manual Unblock Capability**
*For any* IP in the blocklist, an administrator must be able to remove it, and subsequent requests from that IP must not be automatically blocked.
**Validates: Requirements 4.6**

### Attack Pattern Detection Properties

**Property 19: Coordinated Attack Detection**
*For any* set of 50 or more IPs showing identical request patterns within 5 minutes, the system must flag it as a coordinated attack.
**Validates: Requirements 5.2**

**Property 20: Attack Signature Creation**
*For any* detected coordinated attack, an attack signature must be created and stored on the blockchain.
**Validates: Requirements 5.3, 5.4**

**Property 21: Signature Matching Score Boost**
*For any* request matching a known attack signature, the threat score must be increased by 30 points.
**Validates: Requirements 5.5**

### CAPTCHA Properties

**Property 22: CAPTCHA Triggering**
*For any* request with threat score between 40 and 60 (inclusive), a CAPTCHA challenge must be presented.
**Validates: Requirements 6.1**

**Property 23: CAPTCHA Success Processing**
*For any* request with valid CAPTCHA token, the request must be allowed to proceed regardless of threat score (if score < 60).
**Validates: Requirements 6.2**

**Property 24: CAPTCHA Failure Blocking**
*For any* IP that fails CAPTCHA 3 times, the IP must be temporarily blocked for 15 minutes.
**Validates: Requirements 6.3**

**Property 25: Authenticated User CAPTCHA Exemption**
*For any* authenticated user with established session, CAPTCHA must not be required even if threat score is in medium range.
**Validates: Requirements 6.5**

### Dashboard and Admin Properties

**Property 26: Top Threats Ranking**
*For any* query for top threats, the result must contain the 10 IPs with highest threat scores, ordered by score descending.
**Validates: Requirements 7.3**

**Property 27: Time-Series Data Accuracy**
*For any* time window, the requests-per-minute aggregation must accurately reflect the actual request counts in each minute.
**Validates: Requirements 7.4**

**Property 28: Admin Block/Unblock Operations**
*For any* administrator action to block or unblock an IP, the operation must succeed and be reflected in both database and blockchain.
**Validates: Requirements 7.6**

### Patient Management Properties

**Property 29: Patient Record Completeness**
*For any* patient registration, the created record must contain name, date of birth, contact information, and universal patient ID.
**Validates: Requirements 8.1**

**Property 30: Appointment-Patient Association**
*For any* appointment created, it must be associated with exactly one patient using their universal patient ID.
**Validates: Requirements 8.2**

**Property 31: Role-Based Access Control**
*For any* user attempting to access patient data, access must be granted only if the user has an appropriate role (doctor, nurse, or admin).
**Validates: Requirements 8.5**

### Blockchain Integration Properties

**Property 32: Transaction Confirmation Ordering**
*For any* blockchain write operation, the local database must not be updated until the blockchain transaction is confirmed.
**Validates: Requirements 9.3**

**Property 33: Blockchain Caching**
*For any* blockchain read operation performed twice within the cache TTL, the second read must use cached data without making an RPC call.
**Validates: Requirements 9.4**

**Property 34: Fault Tolerance**
*For any* blockchain connection failure, the system must continue operating using cached data and must not crash.
**Validates: Requirements 9.5**

### Rate Limiting Properties

**Property 35: Unauthenticated Rate Limit Enforcement**
*For any* unauthenticated IP making more than 100 requests per minute, the 101st request must be rejected with HTTP 429 status.
**Validates: Requirements 10.1, 10.3**

**Property 36: Authenticated Rate Limit Enforcement**
*For any* authenticated user making more than 500 requests per minute, the 501st request must be rejected with HTTP 429 status.
**Validates: Requirements 10.2, 10.3**

**Property 37: Rate Limit Threat Score Impact**
*For any* IP that consistently exceeds rate limits, the threat score must be increased.
**Validates: Requirements 10.5**

### Auto-Blocking Properties

**Property 38: High Score Auto-Block**
*For any* request with threat score exceeding 80, the IP must be automatically added to the blockchain blocklist.
**Validates: Requirements 11.1**

**Property 39: Auto-Block Expiration**
*For any* automatically blocked IP, the blocklist entry must have an expiration time of 24 hours from the block time.
**Validates: Requirements 11.2**

**Property 40: Manual Block Persistence**
*For any* IP manually blocked by an administrator, the block must not have an automatic expiration.
**Validates: Requirements 11.4**

**Property 41: Unblock Score Reset**
*For any* IP that is unblocked, the threat score for that IP must be reset to 0.
**Validates: Requirements 11.5**

### Cross-Branch Synchronization Properties

**Property 42: Attack Signature Sharing**
*For any* attack signature created at one branch, it must be visible on the blockchain to all other branches.
**Validates: Requirements 12.2**

**Property 43: New Branch Synchronization**
*For any* new branch joining the network, it must successfully read and process all existing blockchain data (patient IDs, blocked IPs, attack signatures).
**Validates: Requirements 12.3**

**Property 44: Offline Queue and Sync**
*For any* branch that goes offline and comes back online, queued updates must be synchronized to the blockchain.
**Validates: Requirements 12.5**


## Error Handling

### Blockchain Connection Errors

**Scenario**: Hardhat node is not running or connection fails

**Handling**:
1. Log error with full stack trace
2. Return cached blockchain data if available
3. Queue write operations for retry when connection restored
4. Display warning in admin dashboard
5. Continue serving requests using local database

**Implementation**:
```python
try:
    result = blockchain_service.register_patient(patient_id_hash)
except Web3Exception as e:
    logger.error(f"Blockchain connection failed: {e}")
    # Mark for retry
    patient.blockchain_sync_pending = True
    patient.save()
    # Continue with local operation
    return success_response
```

### Transaction Confirmation Timeout

**Scenario**: Blockchain transaction takes too long to confirm

**Handling**:
1. Set timeout of 30 seconds for transaction confirmation
2. If timeout exceeded, mark transaction as pending
3. Background task checks transaction status periodically
4. Update database when confirmation received
5. Alert admin if transaction fails after multiple retries

### Redis Connection Errors

**Scenario**: Redis server is unavailable

**Handling**:
1. Fall back to in-memory rate limiting (less accurate but functional)
2. Log warning about degraded performance
3. Attempt reconnection every 60 seconds
4. Display warning in admin dashboard

**Implementation**:
```python
try:
    count = redis_client.incr(f"rate:{ip}")
except RedisConnectionError:
    # Fall back to in-memory tracking
    count = in_memory_rate_tracker.increment(ip)
    logger.warning("Redis unavailable, using in-memory rate limiting")
```

### Invalid Patient Data

**Scenario**: Patient registration with missing or invalid data

**Handling**:
1. Validate all required fields before processing
2. Return HTTP 400 with detailed error messages
3. Do not create partial records
4. Log validation errors for monitoring

**Validation Rules**:
- Name: Required, 2-100 characters
- Date of birth: Required, valid date, not in future
- Email: Required, valid email format
- Phone: Required, valid phone format
- Gender: Required, from allowed choices

### Duplicate Patient Registration

**Scenario**: Attempting to register patient with existing blockchain ID

**Handling**:
1. Check blockchain before registration
2. If ID exists, return HTTP 409 Conflict
3. Provide existing patient ID in response
4. Log duplicate attempt for security monitoring

### CAPTCHA Verification Failure

**Scenario**: Invalid or expired CAPTCHA token

**Handling**:
1. Return HTTP 429 with new CAPTCHA challenge
2. Increment CAPTCHA failure counter for IP
3. After 3 failures, temporarily block IP
4. Log failures for pattern analysis

### Smart Contract Revert

**Scenario**: Smart contract function reverts (e.g., duplicate entry)

**Handling**:
1. Catch revert exception
2. Parse revert reason from error message
3. Return appropriate HTTP status (400 or 409)
4. Do not update local database
5. Log revert for debugging

### High Load Scenarios

**Scenario**: System under heavy legitimate load

**Handling**:
1. Implement request queuing with max queue size
2. Return HTTP 503 Service Unavailable when queue full
3. Scale Redis and database connections
4. Temporarily increase rate limits for authenticated users
5. Monitor and alert on sustained high load

### Database Transaction Failures

**Scenario**: Database write fails due to constraint violation or connection issue

**Handling**:
1. Wrap all database operations in transactions
2. Roll back on any error
3. Return HTTP 500 with generic error message (don't expose internals)
4. Log detailed error for debugging
5. Retry transient errors (connection issues) up to 3 times

### Blockchain Gas Estimation Errors

**Scenario**: Cannot estimate gas for transaction (local network issue)

**Handling**:
1. Use fixed gas limit for local Hardhat network
2. Log estimation failure
3. Proceed with transaction using default gas
4. Monitor for out-of-gas errors

**Implementation**:
```python
try:
    gas_estimate = contract.functions.blockIP(ip_hash).estimate_gas()
except Exception as e:
    logger.warning(f"Gas estimation failed: {e}")
    gas_estimate = 500000  # Default for local network
```


## Testing Strategy

### Dual Testing Approach

This project requires both unit tests and property-based tests to ensure comprehensive correctness:

**Unit Tests**: Verify specific examples, edge cases, and error conditions
- Test specific threat score calculations with known inputs
- Test error handling paths
- Test API endpoint responses
- Test database constraints
- Test integration between components

**Property-Based Tests**: Verify universal properties across all inputs
- Test that threat scoring is consistent and monotonic
- Test that blockchain operations maintain invariants
- Test that patient IDs are always unique
- Test that rate limiting works for any request pattern
- Test that security logging captures all required data

Both testing approaches are complementary and necessary. Unit tests catch concrete bugs with specific inputs, while property-based tests verify that the system behaves correctly across the entire input space.

### Property-Based Testing Framework

**Framework**: Hypothesis (Python)

Hypothesis is the standard property-based testing library for Python. It integrates seamlessly with pytest and provides powerful generators for creating test data.

**Installation**:
```bash
pip install hypothesis pytest pytest-django
```

**Configuration**:
Each property test must run a minimum of 100 iterations to ensure adequate coverage of the input space. This is configured using the `@settings` decorator:

```python
from hypothesis import given, settings, strategies as st

@settings(max_examples=100)
@given(patient_data=st.fixed_dictionaries({
    'name': st.text(min_size=2, max_size=100),
    'dob': st.dates(min_value=date(1900, 1, 1), max_value=date.today()),
    'email': st.emails()
}))
def test_patient_id_uniqueness(patient_data):
    # Test implementation
    pass
```

### Test Organization

**Directory Structure**:
```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_middleware.py
│   ├── test_blockchain_service.py
│   └── test_threat_calculator.py
├── property/
│   ├── test_patient_properties.py
│   ├── test_threat_scoring_properties.py
│   ├── test_blocklist_properties.py
│   ├── test_rate_limiting_properties.py
│   └── test_blockchain_properties.py
├── integration/
│   ├── test_patient_registration_flow.py
│   ├── test_security_flow.py
│   └── test_cross_branch_sync.py
└── conftest.py  # Shared fixtures
```

### Property Test Tagging

Each property-based test must include a comment tag referencing the design document property it validates:

```python
@settings(max_examples=100)
@given(...)
def test_patient_id_uniqueness(...):
    """
    Feature: blockchain-healthcare-security, Property 1: Patient ID Uniqueness
    
    For any two different patients with different registration data,
    the generated blockchain IDs must be unique.
    """
    # Test implementation
```

### Test Fixtures

**Blockchain Fixture** (conftest.py):
```python
import pytest
from web3 import Web3
from eth_tester import EthereumTester

@pytest.fixture(scope="session")
def blockchain():
    """Provide a test blockchain instance"""
    tester = EthereumTester()
    w3 = Web3(Web3.EthereumTesterProvider(tester))
    return w3

@pytest.fixture(scope="session")
def deployed_contracts(blockchain):
    """Deploy all contracts to test blockchain"""
    # Deploy PatientRegistry
    # Deploy BlockedIPRegistry
    # Deploy AttackSignatureRegistry
    return {
        'patient_registry': patient_contract,
        'blocked_ip_registry': ip_contract,
        'attack_signature_registry': sig_contract
    }
```

**Redis Fixture**:
```python
@pytest.fixture
def redis_client():
    """Provide a Redis client for testing"""
    import fakeredis
    return fakeredis.FakeRedis(decode_responses=True)
```

**Django Test Database**:
```python
@pytest.fixture
def db_with_branches(db):
    """Create test branches"""
    from core.models import Branch
    Branch.objects.create(name="Branch A", location="Location A")
    Branch.objects.create(name="Branch B", location="Location B")
```

### Example Property Tests

**Property 1: Patient ID Uniqueness**
```python
from hypothesis import given, settings, strategies as st
from datetime import date

@settings(max_examples=100)
@given(
    patient1=st.fixed_dictionaries({
        'name': st.text(min_size=2, max_size=100),
        'dob': st.dates(min_value=date(1900, 1, 1), max_value=date.today()),
        'email': st.emails()
    }),
    patient2=st.fixed_dictionaries({
        'name': st.text(min_size=2, max_size=100),
        'dob': st.dates(min_value=date(1900, 1, 1), max_value=date.today()),
        'email': st.emails()
    })
)
def test_patient_id_uniqueness(patient1, patient2):
    """
    Feature: blockchain-healthcare-security, Property 1: Patient ID Uniqueness
    
    For any two different patients with different registration data,
    the generated blockchain IDs must be unique.
    """
    from core.models import Patient
    
    # Ensure patients are different
    if patient1 == patient2:
        return
    
    id1 = Patient.generate_blockchain_id_static(
        patient1['name'], patient1['dob'], patient1['email']
    )
    id2 = Patient.generate_blockchain_id_static(
        patient2['name'], patient2['dob'], patient2['email']
    )
    
    assert id1 != id2, "Different patients must have different blockchain IDs"
```

**Property 7: Rate Score Calculation**
```python
@settings(max_examples=100)
@given(request_count=st.integers(min_value=0, max_value=200))
def test_rate_score_calculation(request_count, redis_client):
    """
    Feature: blockchain-healthcare-security, Property 7: Rate Score Calculation
    
    For any IP address with request rate exceeding 100 per minute,
    the rate score component must be 20 points.
    """
    from firewall.services import ThreatScoreCalculator
    
    calculator = ThreatScoreCalculator(redis_client, None)
    ip = "192.168.1.1"
    
    # Simulate request_count requests
    for _ in range(request_count):
        redis_client.incr(f"rate:{ip}")
    
    score = calculator._calculate_rate_score(ip)
    
    if request_count > 100:
        assert score == 20, f"Rate score should be 20 for {request_count} requests"
    elif request_count > 50:
        assert score == 15
    elif request_count > 30:
        assert score == 10
    else:
        assert score == 0
```

**Property 15: Blocked IP Rejection**
```python
@settings(max_examples=100)
@given(
    ip=st.ip_addresses(v=4).map(str),
    reason=st.text(min_size=1, max_size=200)
)
def test_blocked_ip_rejection(ip, reason, blockchain_service, client):
    """
    Feature: blockchain-healthcare-security, Property 15: Blocked IP Rejection
    
    For any IP address that exists in the blockchain blocklist,
    requests from that IP must be rejected with HTTP 403 status.
    """
    from web3 import Web3
    
    # Block the IP on blockchain
    ip_hash = Web3.keccak(text=ip)
    blockchain_service.block_ip(ip_hash, 86400, reason)
    
    # Attempt request from blocked IP
    response = client.get('/api/patients/', REMOTE_ADDR=ip)
    
    assert response.status_code == 403, f"Blocked IP {ip} should receive 403"
    assert 'blocked' in response.json()['reason'].lower()
```

### Unit Test Examples

**Test Patient Registration**:
```python
def test_patient_registration_creates_blockchain_id(db, blockchain_service):
    """Test that patient registration generates blockchain ID"""
    from core.models import Patient, Branch
    
    branch = Branch.objects.create(name="Test Branch", location="Test")
    patient = Patient.objects.create(
        name="John Doe",
        date_of_birth=date(1990, 1, 1),
        gender="M",
        contact_email="john@example.com",
        branch=branch
    )
    
    assert patient.blockchain_id is not None
    assert len(patient.blockchain_id) == 66  # 0x + 64 hex chars
```

**Test Threat Score Calculation**:
```python
def test_threat_score_includes_all_factors(redis_client, blockchain_service):
    """Test that threat score calculation includes all required factors"""
    from firewall.services import ThreatScoreCalculator
    from django.test import RequestFactory
    
    calculator = ThreatScoreCalculator(redis_client, blockchain_service)
    factory = RequestFactory()
    request = factory.get('/api/patients/')
    
    score, factors = calculator.calculate_threat_score(request, "192.168.1.1")
    
    # Verify all factors are present
    assert 'rate' in factors
    assert 'pattern' in factors
    assert 'session' in factors
    assert 'entropy' in factors
    assert 'auth_failures' in factors
    assert len(factors) >= 5
```

### Integration Tests

**Test End-to-End Patient Registration**:
```python
def test_patient_registration_flow(client, blockchain_service, db):
    """Test complete patient registration including blockchain"""
    response = client.post('/api/patients/', {
        'name': 'Jane Smith',
        'date_of_birth': '1985-05-15',
        'gender': 'F',
        'contact_email': 'jane@example.com',
        'contact_phone': '+1234567890',
        'address': '123 Main St',
        'branch': 1
    })
    
    assert response.status_code == 201
    patient_id = response.json()['blockchain_id']
    
    # Verify blockchain registration
    from web3 import Web3
    patient_hash = Web3.keccak(text=patient_id)
    assert blockchain_service.is_patient_registered(patient_hash)
```

**Test Security Flow**:
```python
def test_high_threat_request_blocked(client, redis_client):
    """Test that high threat requests are blocked"""
    ip = "192.168.1.100"
    
    # Generate high threat score by making many requests
    for _ in range(150):
        client.get('/api/patients/', REMOTE_ADDR=ip)
    
    # Next request should be blocked
    response = client.get('/api/patients/', REMOTE_ADDR=ip)
    assert response.status_code == 403
```

### Running Tests

**Run all tests**:
```bash
pytest
```

**Run only property tests**:
```bash
pytest tests/property/
```

**Run with coverage**:
```bash
pytest --cov=core --cov=firewall --cov-report=html
```

**Run specific property test**:
```bash
pytest tests/property/test_patient_properties.py::test_patient_id_uniqueness -v
```

### Continuous Integration

Tests should be run automatically on every commit using GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install hypothesis pytest pytest-django pytest-cov
      - name: Run tests
        run: pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

