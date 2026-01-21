"""
BlockchainService for interacting with Hardhat local blockchain.
Handles patient registration and IP blocking on-chain.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from django.conf import settings
from web3 import Web3
from web3.exceptions import TransactionNotFound, TimeExhausted
import redis

logger = logging.getLogger('blockchain')


class BlockchainService:
    """
    Service for interacting with Hardhat local blockchain.
    Handles patient registration and IP blocking on-chain.
    """
    
    def __init__(self):
        """Initialize blockchain connection and load contracts."""
        # Connect to local Hardhat network
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
        
        # Note: Hardhat doesn't require PoA middleware in newer versions
        
        # Verify connection
        self.connected = False
        try:
            if self.w3.is_connected():
                logger.info(f"Connected to blockchain network. Latest block: {self.w3.eth.block_number}")
                self.connected = True
                
                # Load contract instances
                self.patient_registry = self._load_contract('PatientRegistry')
                self.blocked_ip_registry = self._load_contract('BlockedIPRegistry')
                self.attack_signature_registry = self._load_contract('AttackSignatureRegistry')
                
                # Use first account from Hardhat for transactions
                self.account = self.w3.eth.accounts[0]
                logger.info(f"Using account: {self.account}")
            else:
                logger.warning("Blockchain network not available - operating in offline mode")
                self.patient_registry = None
                self.blocked_ip_registry = None
                self.attack_signature_registry = None
                self.account = None
        except Exception as e:
            logger.warning(f"Blockchain connection failed: {e} - operating in offline mode")
            self.connected = False
            self.patient_registry = None
            self.blocked_ip_registry = None
            self.attack_signature_registry = None
            self.account = None
        
        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # Cache timeout for blockchain reads (5 minutes)
        self.cache_timeout = 300
        
    def _load_contract(self, contract_name: str):
        """Load contract ABI and create contract instance."""
        try:
            # Load contract ABI
            if contract_name == 'BlockedIPRegistry':
                abi_path = Path('caregrid_chain/artifacts/contracts/BlockedIP.sol/BlockedIPRegistry.json')
            else:
                abi_path = Path(f'caregrid_chain/artifacts/contracts/{contract_name}.sol/{contract_name}.json')
            
            with open(abi_path) as f:
                contract_json = json.load(f)
            
            # Load deployed address
            deployment_path = Path('caregrid_chain/deployments/all-contracts.json')
            with open(deployment_path) as f:
                deployment = json.load(f)
            
            contract_address = deployment[contract_name]
            
            contract = self.w3.eth.contract(
                address=contract_address,
                abi=contract_json['abi']
            )
            
            logger.info(f"Loaded {contract_name} contract at {contract_address}")
            return contract
            
        except Exception as e:
            logger.error(f"Failed to load {contract_name} contract: {e}")
            raise
    
    def _wait_for_transaction_receipt(self, tx_hash: str, timeout: int = None) -> Dict:
        """Wait for transaction confirmation with timeout."""
        timeout = timeout or settings.BLOCKCHAIN_CONFIRMATION_TIMEOUT
        
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash, 
                timeout=timeout
            )
            
            if receipt.status == 1:
                logger.info(f"Transaction {tx_hash} confirmed successfully")
            else:
                logger.error(f"Transaction {tx_hash} failed")
                
            return receipt
            
        except TimeExhausted:
            logger.error(f"Transaction {tx_hash} timed out after {timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"Error waiting for transaction {tx_hash}: {e}")
            raise
    
    def _retry_transaction(self, func, *args, max_retries: int = 3, **kwargs):
        """Retry blockchain transaction with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Transaction failed after {max_retries} attempts: {e}")
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Transaction attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    
    def _cache_get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            cached_value = self.redis_client.get(key)
            if cached_value:
                return json.loads(cached_value)
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
        return None
    
    def _cache_set(self, key: str, value: Any, timeout: int = None) -> None:
        """Set value in Redis cache."""
        try:
            timeout = timeout or self.cache_timeout
            self.redis_client.setex(
                key, 
                timeout, 
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
    
    # Patient Registration Methods
    
    def register_patient(self, patient_id_hash: str) -> Tuple[Optional[str], bool]:
        """
        Register patient ID on blockchain.
        
        Args:
            patient_id_hash: Hashed patient ID (bytes32 hex string)
            
        Returns:
            Tuple of (transaction_hash, success_status)
        """
        # If blockchain is not connected, return failure but don't crash
        if not self.connected or not self.patient_registry:
            logger.warning("Blockchain not available - patient registration skipped")
            return None, False
            
        try:
            # Convert hex string to bytes32 if needed
            if isinstance(patient_id_hash, str):
                if patient_id_hash.startswith('0x'):
                    patient_id_bytes = bytes.fromhex(patient_id_hash[2:])
                else:
                    patient_id_bytes = bytes.fromhex(patient_id_hash)
            else:
                patient_id_bytes = patient_id_hash
            
            logger.info(f"Registering patient with ID hash: {patient_id_hash}")
            
            # Check if already registered (with caching)
            if self.is_patient_registered(patient_id_hash):
                logger.warning(f"Patient {patient_id_hash} already registered")
                return None, False
            
            def _register_transaction():
                tx_hash = self.patient_registry.functions.registerPatient(
                    patient_id_bytes
                ).transact({
                    'from': self.account,
                    'gas': settings.BLOCKCHAIN_GAS_LIMIT
                })
                return tx_hash
            
            # Execute transaction with retry logic
            tx_hash = self._retry_transaction(_register_transaction)
            
            # Wait for confirmation
            receipt = self._wait_for_transaction_receipt(tx_hash.hex())
            
            success = receipt.status == 1
            if success:
                # Clear cache for this patient
                cache_key = f"patient_registered:{patient_id_hash}"
                self.redis_client.delete(cache_key)
                logger.info(f"Patient {patient_id_hash} registered successfully")
            
            return tx_hash.hex(), success
            
        except Exception as e:
            logger.error(f"Failed to register patient {patient_id_hash}: {e}")
            return None, False
    
    def is_patient_registered(self, patient_id_hash: str) -> bool:
        """
        Check if patient is registered on blockchain.
        
        Args:
            patient_id_hash: Hashed patient ID (bytes32 hex string)
            
        Returns:
            True if patient is registered, False otherwise
        """
        # If blockchain is not connected, return False (assume not registered)
        if not self.connected or not self.patient_registry:
            logger.warning("Blockchain not available - assuming patient not registered")
            return False
            
        try:
            # Check cache first
            cache_key = f"patient_registered:{patient_id_hash}"
            cached_result = self._cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Convert hex string to bytes32 if needed
            if isinstance(patient_id_hash, str):
                if patient_id_hash.startswith('0x'):
                    patient_id_bytes = bytes.fromhex(patient_id_hash[2:])
                else:
                    patient_id_bytes = bytes.fromhex(patient_id_hash)
            else:
                patient_id_bytes = patient_id_hash
            
            # Query blockchain
            is_registered = self.patient_registry.functions.isPatientRegistered(
                patient_id_bytes
            ).call()
            
            # Cache result
            self._cache_set(cache_key, is_registered)
            
            return is_registered
            
        except Exception as e:
            logger.error(f"Failed to check patient registration {patient_id_hash}: {e}")
            # Return cached result if available, otherwise False
            cache_key = f"patient_registered:{patient_id_hash}"
            cached_result = self._cache_get(cache_key)
            return cached_result if cached_result is not None else False
    
    def get_patient_info(self, patient_id_hash: str) -> Optional[Dict]:
        """
        Get patient information from blockchain.
        
        Args:
            patient_id_hash: Hashed patient ID (bytes32 hex string)
            
        Returns:
            Dictionary with patient info or None if not found
        """
        try:
            # Check cache first
            cache_key = f"patient_info:{patient_id_hash}"
            cached_result = self._cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Convert hex string to bytes32 if needed
            if isinstance(patient_id_hash, str):
                if patient_id_hash.startswith('0x'):
                    patient_id_bytes = bytes.fromhex(patient_id_hash[2:])
                else:
                    patient_id_bytes = bytes.fromhex(patient_id_hash)
            else:
                patient_id_bytes = patient_id_hash
            
            # Query blockchain
            patient_data = self.patient_registry.functions.getPatient(
                patient_id_bytes
            ).call()
            
            if not patient_data or not patient_data[3]:  # isActive field
                return None
            
            patient_info = {
                'patient_id_hash': patient_data[0].hex(),
                'registration_time': patient_data[1],
                'registered_by': patient_data[2],
                'is_active': patient_data[3]
            }
            
            # Cache result
            self._cache_set(cache_key, patient_info)
            
            return patient_info
            
        except Exception as e:
            logger.error(f"Failed to get patient info {patient_id_hash}: {e}")
            # Return cached result if available
            cache_key = f"patient_info:{patient_id_hash}"
            return self._cache_get(cache_key)
    
    # IP Blocking Methods
    
    def block_ip(self, ip_hash: str, duration_seconds: int, reason: str, is_manual: bool = False) -> Tuple[Optional[str], bool]:
        """
        Add IP to blockchain blocklist.
        
        Args:
            ip_hash: Hashed IP address (bytes32 hex string)
            duration_seconds: Block duration in seconds
            reason: Reason for blocking
            is_manual: Whether this is a manual block (vs automatic)
            
        Returns:
            Tuple of (transaction_hash, success_status)
        """
        try:
            # Convert hex string to bytes32 if needed
            if isinstance(ip_hash, str):
                if ip_hash.startswith('0x'):
                    ip_bytes = bytes.fromhex(ip_hash[2:])
                else:
                    ip_bytes = bytes.fromhex(ip_hash)
            else:
                ip_bytes = ip_hash
            
            logger.info(f"Blocking IP {ip_hash} for {duration_seconds}s: {reason}")
            
            # Check if already blocked
            if self.is_ip_blocked(ip_hash):
                logger.warning(f"IP {ip_hash} already blocked")
                return None, False
            
            def _block_transaction():
                tx_hash = self.blocked_ip_registry.functions.blockIP(
                    ip_bytes,
                    duration_seconds,
                    reason,
                    is_manual
                ).transact({
                    'from': self.account,
                    'gas': settings.BLOCKCHAIN_GAS_LIMIT
                })
                return tx_hash
            
            # Execute transaction with retry logic
            tx_hash = self._retry_transaction(_block_transaction)
            
            # Wait for confirmation
            receipt = self._wait_for_transaction_receipt(tx_hash.hex())
            
            success = receipt.status == 1
            if success:
                # Clear cache for this IP
                cache_key = f"ip_blocked:{ip_hash}"
                self.redis_client.delete(cache_key)
                logger.info(f"IP {ip_hash} blocked successfully")
            
            return tx_hash.hex(), success
            
        except Exception as e:
            logger.error(f"Failed to block IP {ip_hash}: {e}")
            return None, False
    
    def is_ip_blocked(self, ip_hash: str) -> bool:
        """
        Check if IP is blocked on blockchain.
        
        Args:
            ip_hash: Hashed IP address (bytes32 hex string)
            
        Returns:
            True if IP is blocked, False otherwise
        """
        try:
            # Check cache first
            cache_key = f"ip_blocked:{ip_hash}"
            cached_result = self._cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Convert hex string to bytes32 if needed
            if isinstance(ip_hash, str):
                if ip_hash.startswith('0x'):
                    ip_bytes = bytes.fromhex(ip_hash[2:])
                else:
                    ip_bytes = bytes.fromhex(ip_hash)
            else:
                ip_bytes = ip_hash
            
            # Query blockchain
            is_blocked = self.blocked_ip_registry.functions.isIPBlocked(
                ip_bytes
            ).call()
            
            # Cache result for shorter time (1 minute) since blocks can expire
            self._cache_set(cache_key, is_blocked, timeout=60)
            
            return is_blocked
            
        except Exception as e:
            logger.error(f"Failed to check IP block status {ip_hash}: {e}")
            # Return cached result if available, otherwise False
            cache_key = f"ip_blocked:{ip_hash}"
            cached_result = self._cache_get(cache_key)
            return cached_result if cached_result is not None else False
    
    def unblock_ip(self, ip_hash: str) -> Tuple[Optional[str], bool]:
        """
        Remove IP from blockchain blocklist.
        
        Args:
            ip_hash: Hashed IP address (bytes32 hex string)
            
        Returns:
            Tuple of (transaction_hash, success_status)
        """
        try:
            # Convert hex string to bytes32 if needed
            if isinstance(ip_hash, str):
                if ip_hash.startswith('0x'):
                    ip_bytes = bytes.fromhex(ip_hash[2:])
                else:
                    ip_bytes = bytes.fromhex(ip_hash)
            else:
                ip_bytes = ip_hash
            
            logger.info(f"Unblocking IP {ip_hash}")
            
            # Check if actually blocked
            if not self.is_ip_blocked(ip_hash):
                logger.warning(f"IP {ip_hash} not currently blocked")
                return None, False
            
            def _unblock_transaction():
                tx_hash = self.blocked_ip_registry.functions.unblockIP(
                    ip_bytes
                ).transact({
                    'from': self.account,
                    'gas': settings.BLOCKCHAIN_GAS_LIMIT
                })
                return tx_hash
            
            # Execute transaction with retry logic
            tx_hash = self._retry_transaction(_unblock_transaction)
            
            # Wait for confirmation
            receipt = self._wait_for_transaction_receipt(tx_hash.hex())
            
            success = receipt.status == 1
            if success:
                # Clear cache for this IP
                cache_key = f"ip_blocked:{ip_hash}"
                self.redis_client.delete(cache_key)
                logger.info(f"IP {ip_hash} unblocked successfully")
            
            return tx_hash.hex(), success
            
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip_hash}: {e}")
            return None, False
    
    def get_blocked_ip_info(self, ip_hash: str) -> Optional[Dict]:
        """
        Get blocked IP information from blockchain.
        
        Args:
            ip_hash: Hashed IP address (bytes32 hex string)
            
        Returns:
            Dictionary with block info or None if not found
        """
        try:
            # Check cache first
            cache_key = f"ip_block_info:{ip_hash}"
            cached_result = self._cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Convert hex string to bytes32 if needed
            if isinstance(ip_hash, str):
                if ip_hash.startswith('0x'):
                    ip_bytes = bytes.fromhex(ip_hash[2:])
                else:
                    ip_bytes = bytes.fromhex(ip_hash)
            else:
                ip_bytes = ip_hash
            
            # Query blockchain
            block_data = self.blocked_ip_registry.functions.getBlockEntry(
                ip_bytes
            ).call()
            
            if not block_data or not block_data[0]:  # Check if entry exists
                return None
            
            block_info = {
                'ip_hash': block_data[0].hex(),
                'block_time': block_data[1],
                'expiry_time': block_data[2],
                'reason': block_data[3],
                'blocked_by': block_data[4],
                'is_manual': block_data[5]
            }
            
            # Cache result for shorter time (1 minute)
            self._cache_set(cache_key, block_info, timeout=60)
            
            return block_info
            
        except Exception as e:
            logger.error(f"Failed to get IP block info {ip_hash}: {e}")
            # Return cached result if available
            cache_key = f"ip_block_info:{ip_hash}"
            return self._cache_get(cache_key)
    
    def cleanup_expired_blocks(self) -> Tuple[Optional[str], bool]:
        """
        Clean up expired IP blocks on blockchain.
        
        Returns:
            Tuple of (transaction_hash, success_status)
        """
        try:
            logger.info("Cleaning up expired IP blocks")
            
            def _cleanup_transaction():
                tx_hash = self.blocked_ip_registry.functions.cleanupExpiredBlocks().transact({
                    'from': self.account,
                    'gas': settings.BLOCKCHAIN_GAS_LIMIT
                })
                return tx_hash
            
            # Execute transaction with retry logic
            tx_hash = self._retry_transaction(_cleanup_transaction)
            
            # Wait for confirmation
            receipt = self._wait_for_transaction_receipt(tx_hash.hex())
            
            success = receipt.status == 1
            if success:
                # Clear all IP block caches since blocks may have been removed
                pattern = "ip_blocked:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                logger.info("Expired IP blocks cleaned up successfully")
            
            return tx_hash.hex(), success
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired blocks: {e}")
            return None, False
    
    # Attack Signature Methods
    
    def add_attack_signature(self, pattern_json: str, severity: int) -> Tuple[Optional[str], bool]:
        """
        Add attack signature to blockchain.
        
        Args:
            pattern_json: JSON string describing attack pattern
            severity: Severity level (1-10)
            
        Returns:
            Tuple of (transaction_hash, success_status)
        """
        try:
            logger.info(f"Adding attack signature with severity {severity}")
            
            # Validate severity
            if not (1 <= severity <= 10):
                logger.error(f"Invalid severity level: {severity}. Must be 1-10")
                return None, False
            
            # Validate JSON
            try:
                json.loads(pattern_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON pattern: {e}")
                return None, False
            
            def _add_signature_transaction():
                tx_hash = self.attack_signature_registry.functions.addSignature(
                    pattern_json,
                    severity
                ).transact({
                    'from': self.account,
                    'gas': settings.BLOCKCHAIN_GAS_LIMIT
                })
                return tx_hash
            
            # Execute transaction with retry logic
            tx_hash = self._retry_transaction(_add_signature_transaction)
            
            # Wait for confirmation
            receipt = self._wait_for_transaction_receipt(tx_hash.hex())
            
            success = receipt.status == 1
            if success:
                # Clear signatures cache
                self.redis_client.delete("attack_signatures:all")
                logger.info("Attack signature added successfully")
            
            return tx_hash.hex(), success
            
        except Exception as e:
            logger.error(f"Failed to add attack signature: {e}")
            return None, False
    
    def get_attack_signatures(self) -> List[Dict]:
        """
        Retrieve all attack signatures from blockchain.
        
        Returns:
            List of signature dictionaries
        """
        try:
            # Check cache first
            cache_key = "attack_signatures:all"
            cached_result = self._cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Get all signature hashes
            signature_hashes = self.attack_signature_registry.functions.getAllSignatures().call()
            
            signatures = []
            for sig_hash in signature_hashes:
                try:
                    # Get signature details
                    sig_data = self.attack_signature_registry.functions.getSignature(sig_hash).call()
                    
                    if sig_data and sig_data[0]:  # Check if signature exists
                        signature_info = {
                            'hash': sig_data[0].hex(),
                            'pattern': json.loads(sig_data[1]),  # Parse JSON pattern
                            'detected_time': sig_data[2],
                            'reported_by': sig_data[3],
                            'severity': sig_data[4]
                        }
                        signatures.append(signature_info)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse signature {sig_hash.hex()}: {e}")
                    continue
            
            # Cache result
            self._cache_set(cache_key, signatures)
            
            return signatures
            
        except Exception as e:
            logger.error(f"Failed to get attack signatures: {e}")
            # Return cached result if available
            cached_result = self._cache_get("attack_signatures:all")
            return cached_result if cached_result is not None else []
    
    def get_attack_signatures_by_severity(self, min_severity: int) -> List[Dict]:
        """
        Retrieve attack signatures with minimum severity level.
        
        Args:
            min_severity: Minimum severity level (1-10)
            
        Returns:
            List of signature dictionaries
        """
        try:
            # Check cache first
            cache_key = f"attack_signatures:severity_{min_severity}"
            cached_result = self._cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Get signature hashes by severity
            signature_hashes = self.attack_signature_registry.functions.getSignaturesBySeverity(
                min_severity
            ).call()
            
            signatures = []
            for sig_hash in signature_hashes:
                try:
                    # Get signature details
                    sig_data = self.attack_signature_registry.functions.getSignature(sig_hash).call()
                    
                    if sig_data and sig_data[0]:  # Check if signature exists
                        signature_info = {
                            'hash': sig_data[0].hex(),
                            'pattern': json.loads(sig_data[1]),  # Parse JSON pattern
                            'detected_time': sig_data[2],
                            'reported_by': sig_data[3],
                            'severity': sig_data[4]
                        }
                        signatures.append(signature_info)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse signature {sig_hash.hex()}: {e}")
                    continue
            
            # Cache result
            self._cache_set(cache_key, signatures)
            
            return signatures
            
        except Exception as e:
            logger.error(f"Failed to get attack signatures by severity: {e}")
            # Return cached result if available
            cached_result = self._cache_get(f"attack_signatures:severity_{min_severity}")
            return cached_result if cached_result is not None else []
    
    def has_attack_signature(self, signature_hash: str) -> bool:
        """
        Check if attack signature exists on blockchain.
        
        Args:
            signature_hash: Signature hash (bytes32 hex string)
            
        Returns:
            True if signature exists, False otherwise
        """
        try:
            # Convert hex string to bytes32 if needed
            if isinstance(signature_hash, str):
                if signature_hash.startswith('0x'):
                    sig_bytes = bytes.fromhex(signature_hash[2:])
                else:
                    sig_bytes = bytes.fromhex(signature_hash)
            else:
                sig_bytes = signature_hash
            
            # Query blockchain
            exists = self.attack_signature_registry.functions.hasSignature(
                sig_bytes
            ).call()
            
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check signature existence {signature_hash}: {e}")
            return False
    
    def get_signature_count(self) -> int:
        """
        Get total number of attack signatures.
        
        Returns:
            Number of signatures
        """
        try:
            count = self.attack_signature_registry.functions.getSignatureCount().call()
            return count
        except Exception as e:
            logger.error(f"Failed to get signature count: {e}")
            return 0
    
    # Fault Tolerance and Connection Management
    
    def is_connected(self) -> bool:
        """
        Check if blockchain connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            # Try to get latest block number
            self.w3.eth.block_number
            return True
        except Exception as e:
            logger.warning(f"Blockchain connection check failed: {e}")
            return False
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to blockchain network.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        try:
            logger.info("Attempting to reconnect to blockchain network...")
            
            # Reinitialize Web3 connection
            self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
            # Note: Hardhat doesn't require PoA middleware in newer versions
            
            if self.w3.is_connected():
                logger.info("Blockchain reconnection successful")
                return True
            else:
                logger.error("Blockchain reconnection failed")
                return False
                
        except Exception as e:
            logger.error(f"Blockchain reconnection error: {e}")
            return False
    
    def execute_with_fallback(self, blockchain_func, cache_key: str = None, default_value=None):
        """
        Execute blockchain function with fallback to cached data on failure.
        
        Args:
            blockchain_func: Function to execute against blockchain
            cache_key: Redis cache key for fallback data
            default_value: Default value if both blockchain and cache fail
            
        Returns:
            Result from blockchain or cached data
        """
        try:
            # Try blockchain operation first
            if self.is_connected():
                return blockchain_func()
            else:
                # Try to reconnect
                if self.reconnect():
                    return blockchain_func()
                else:
                    raise ConnectionError("Cannot connect to blockchain")
                    
        except Exception as e:
            logger.warning(f"Blockchain operation failed: {e}")
            
            # Fallback to cached data
            if cache_key:
                cached_result = self._cache_get(cache_key)
                if cached_result is not None:
                    logger.info(f"Using cached data for key: {cache_key}")
                    return cached_result
            
            # Return default value if no cache available
            logger.warning(f"No cached data available, returning default: {default_value}")
            return default_value
    
    def get_blockchain_status(self) -> Dict:
        """
        Get comprehensive blockchain connection status.
        
        Returns:
            Dictionary with connection status information
        """
        status = {
            'connected': False,
            'latest_block': None,
            'account': self.account,
            'contracts_loaded': False,
            'network_id': None,
            'error': None
        }
        
        try:
            if self.is_connected():
                status['connected'] = True
                status['latest_block'] = self.w3.eth.block_number
                status['network_id'] = self.w3.eth.chain_id
                
                # Check if contracts are accessible
                try:
                    self.patient_registry.functions.isPatientRegistered(b'\x00' * 32).call()
                    status['contracts_loaded'] = True
                except:
                    status['contracts_loaded'] = False
                    
        except Exception as e:
            status['error'] = str(e)
            
        return status
    
    def health_check(self) -> Dict:
        """
        Perform comprehensive health check of blockchain service.
        
        Returns:
            Dictionary with health check results
        """
        health = {
            'blockchain': self.get_blockchain_status(),
            'redis': {'connected': False, 'error': None},
            'overall_status': 'unhealthy'
        }
        
        # Check Redis connection
        try:
            self.redis_client.ping()
            health['redis']['connected'] = True
        except Exception as e:
            health['redis']['error'] = str(e)
        
        # Determine overall status
        if (health['blockchain']['connected'] and 
            health['blockchain']['contracts_loaded'] and 
            health['redis']['connected']):
            health['overall_status'] = 'healthy'
        elif health['redis']['connected']:
            health['overall_status'] = 'degraded'  # Can use cache
        else:
            health['overall_status'] = 'unhealthy'
            
        return health
    
    def clear_all_caches(self) -> bool:
        """
        Clear all blockchain-related caches.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            patterns = [
                "patient_registered:*",
                "patient_info:*", 
                "ip_blocked:*",
                "ip_block_info:*",
                "attack_signatures:*"
            ]
            
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            logger.info("All blockchain caches cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")
            return False


# Singleton instance for global use
_blockchain_service = None

def get_blockchain_service() -> BlockchainService:
    """
    Get singleton instance of BlockchainService.
    
    Returns:
        BlockchainService instance
    """
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    return _blockchain_service