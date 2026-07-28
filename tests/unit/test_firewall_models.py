"""
Unit tests for firewall models: SecurityLog, BlockedIP, AttackPattern
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from firewall.models import SecurityLog, BlockedIP, AttackPattern

User = get_user_model()


class SecurityLogModelTest(TestCase):
    """Test cases for SecurityLog model"""
    
    def test_security_log_creation(self):
        """Test basic security log creation"""
        log = SecurityLog.objects.create(
            ip_address="192.168.1.100",
            threat_score=45,
            threat_level="MEDIUM",
            endpoint="/api/patients/",
            method="GET",
            user_agent="Mozilla/5.0 Test Browser",
            action_taken="captcha"
        )
        
        self.assertEqual(log.ip_address, "192.168.1.100")
        self.assertEqual(log.threat_score, 45)
        self.assertEqual(log.threat_level, "MEDIUM")
        self.assertEqual(log.endpoint, "/api/patients/")
        self.assertEqual(log.method, "GET")
        self.assertEqual(log.action_taken, "captcha")
        self.assertIsNotNone(log.timestamp)
    
    def test_security_log_default_values(self):
        """Test security log default values"""
        log = SecurityLog.objects.create(
            ip_address="10.0.0.1",
            threat_score=20,
            threat_level="LOW",
            endpoint="/api/test/",
            method="POST",
            user_agent="Test Agent",
            action_taken="allowed"
        )
        
        self.assertEqual(log.rate_score, 0)
        self.assertEqual(log.pattern_score, 0)
        self.assertEqual(log.session_score, 0)
        self.assertEqual(log.entropy_score, 0)
        self.assertEqual(log.auth_failure_score, 0)
        self.assertFalse(log.blocked_on_blockchain)
        self.assertEqual(log.block_tx_hash, '')
    
    def test_security_log_threat_level_choices(self):
        """Test threat level choices validation"""
        # Valid choices should work
        for level in ['LOW', 'MEDIUM', 'HIGH']:
            log = SecurityLog(
                ip_address="192.168.1.1",
                threat_score=50,
                threat_level=level,
                endpoint="/test/",
                method="GET",
                user_agent="Test",
                action_taken="allowed"
            )
            log.full_clean()  # This should not raise ValidationError
    
    def test_security_log_with_all_factors(self):
        """Test security log with all threat factors"""
        log = SecurityLog.objects.create(
            ip_address="172.16.0.1",
            threat_score=85,
            threat_level="HIGH",
            endpoint="/api/login/",
            method="POST",
            user_agent="Suspicious Bot",
            rate_score=20,
            pattern_score=25,
            session_score=20,
            entropy_score=15,
            auth_failure_score=10,
            action_taken="blocked",
            blocked_on_blockchain=True,
            block_tx_hash="0xabc123def456"
        )
        
        self.assertEqual(log.rate_score, 20)
        self.assertEqual(log.pattern_score, 25)
        self.assertEqual(log.session_score, 20)
        self.assertEqual(log.entropy_score, 15)
        self.assertEqual(log.auth_failure_score, 10)
        self.assertTrue(log.blocked_on_blockchain)
        self.assertEqual(log.block_tx_hash, "0xabc123def456")
    
    def test_security_log_str_representation(self):
        """Test string representation of security log"""
        log = SecurityLog(
            ip_address="192.168.1.1",
            threat_level="HIGH",
            threat_score=75,
            timestamp=timezone.now()
        )
        
        expected_str = f"192.168.1.1 - HIGH (75) at {log.timestamp}"
        self.assertEqual(str(log), expected_str)
    
    def test_security_log_ordering(self):
        """Test security log ordering by timestamp (newest first)"""
        # Create logs with different timestamps
        old_log = SecurityLog.objects.create(
            ip_address="192.168.1.1",
            threat_score=30,
            threat_level="LOW",
            endpoint="/test1/",
            method="GET",
            user_agent="Test",
            action_taken="allowed"
        )
        
        new_log = SecurityLog.objects.create(
            ip_address="192.168.1.2",
            threat_score=60,
            threat_level="HIGH",
            endpoint="/test2/",
            method="POST",
            user_agent="Test",
            action_taken="blocked"
        )
        
        logs = list(SecurityLog.objects.all())
        self.assertEqual(logs[0], new_log)  # Newest first
        self.assertEqual(logs[1], old_log)


class BlockedIPModelTest(TestCase):
    """Test cases for BlockedIP model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
    
    def test_blocked_ip_creation(self):
        """Test basic blocked IP creation"""
        expiry = timezone.now() + timedelta(hours=24)
        blocked_ip = BlockedIP.objects.create(
            ip_address="192.168.1.100",
            ip_hash="0xabc123def456",
            expiry_time=expiry,
            reason="Suspicious activity detected"
        )
        
        self.assertEqual(blocked_ip.ip_address, "192.168.1.100")
        self.assertEqual(blocked_ip.ip_hash, "0xabc123def456")
        self.assertEqual(blocked_ip.expiry_time, expiry)
        self.assertEqual(blocked_ip.reason, "Suspicious activity detected")
        self.assertIsNotNone(blocked_ip.block_time)
    
    def test_blocked_ip_default_values(self):
        """Test blocked IP default values"""
        blocked_ip = BlockedIP.objects.create(
            ip_address="10.0.0.1",
            ip_hash="0x123456",
            expiry_time=timezone.now() + timedelta(hours=1),
            reason="Test block"
        )
        
        self.assertFalse(blocked_ip.is_manual)
        self.assertIsNone(blocked_ip.blocked_by)
        self.assertFalse(blocked_ip.blockchain_synced)
        self.assertEqual(blocked_ip.block_tx_hash, '')
    
    def test_blocked_ip_uniqueness(self):
        """Test IP address uniqueness constraint"""
        expiry = timezone.now() + timedelta(hours=1)
        
        BlockedIP.objects.create(
            ip_address="192.168.1.1",
            ip_hash="0x111",
            expiry_time=expiry,
            reason="First block"
        )
        
        # Creating another block for same IP should fail
        with self.assertRaises(IntegrityError):
            BlockedIP.objects.create(
                ip_address="192.168.1.1",
                ip_hash="0x222",
                expiry_time=expiry,
                reason="Second block"
            )
    
    def test_blocked_ip_manual_block(self):
        """Test manual IP blocking with user"""
        blocked_ip = BlockedIP.objects.create(
            ip_address="172.16.0.1",
            ip_hash="0xmanual123",
            expiry_time=timezone.now() + timedelta(days=7),
            reason="Manual block by admin",
            is_manual=True,
            blocked_by=self.user,
            blockchain_synced=True,
            block_tx_hash="0xtxhash123"
        )
        
        self.assertTrue(blocked_ip.is_manual)
        self.assertEqual(blocked_ip.blocked_by, self.user)
        self.assertTrue(blocked_ip.blockchain_synced)
        self.assertEqual(blocked_ip.block_tx_hash, "0xtxhash123")
    
    def test_blocked_ip_is_expired_property(self):
        """Test is_expired property"""
        # Create expired block
        past_time = timezone.now() - timedelta(hours=1)
        expired_block = BlockedIP.objects.create(
            ip_address="192.168.1.1",
            ip_hash="0xexpired",
            expiry_time=past_time,
            reason="Expired block"
        )
        self.assertTrue(expired_block.is_expired)
        
        # Create active block
        future_time = timezone.now() + timedelta(hours=1)
        active_block = BlockedIP.objects.create(
            ip_address="192.168.1.2",
            ip_hash="0xactive",
            expiry_time=future_time,
            reason="Active block"
        )
        self.assertFalse(active_block.is_expired)
    
    def test_blocked_ip_str_representation(self):
        """Test string representation of blocked IP"""
        expiry = timezone.now() + timedelta(hours=2)
        blocked_ip = BlockedIP(
            ip_address="192.168.1.1",
            expiry_time=expiry
        )
        
        expected_str = f"192.168.1.1 blocked until {expiry}"
        self.assertEqual(str(blocked_ip), expected_str)
    
    def test_blocked_ip_ordering(self):
        """Test blocked IP ordering by block_time (newest first)"""
        old_block = BlockedIP.objects.create(
            ip_address="192.168.1.1",
            ip_hash="0xold",
            expiry_time=timezone.now() + timedelta(hours=1),
            reason="Old block"
        )
        
        new_block = BlockedIP.objects.create(
            ip_address="192.168.1.2",
            ip_hash="0xnew",
            expiry_time=timezone.now() + timedelta(hours=1),
            reason="New block"
        )
        
        blocks = list(BlockedIP.objects.all())
        self.assertEqual(blocks[0], new_block)  # Newest first
        self.assertEqual(blocks[1], old_block)


class AttackPatternModelTest(TestCase):
    """Test cases for AttackPattern model"""
    
    def test_attack_pattern_creation(self):
        """Test basic attack pattern creation"""
        pattern_data = {
            "endpoints": ["/api/login/", "/api/users/"],
            "user_agents": ["Bot1", "Bot2"],
            "request_rate": 150
        }
        
        pattern = AttackPattern.objects.create(
            pattern_hash="0xpattern123",
            pattern_data=pattern_data,
            severity=8,
            ip_count=50,
            request_count=7500
        )
        
        self.assertEqual(pattern.pattern_hash, "0xpattern123")
        self.assertEqual(pattern.pattern_data, pattern_data)
        self.assertEqual(pattern.severity, 8)
        self.assertEqual(pattern.ip_count, 50)
        self.assertEqual(pattern.request_count, 7500)
        self.assertIsNotNone(pattern.detected_at)
    
    def test_attack_pattern_default_values(self):
        """Test attack pattern default values"""
        pattern = AttackPattern.objects.create(
            pattern_hash="0xdefault123",
            pattern_data={"test": "data"},
            severity=5,
            ip_count=10,
            request_count=100
        )
        
        self.assertFalse(pattern.blockchain_synced)
        self.assertEqual(pattern.signature_tx_hash, '')
    
    def test_attack_pattern_uniqueness(self):
        """Test pattern hash uniqueness constraint"""
        AttackPattern.objects.create(
            pattern_hash="0xunique123",
            pattern_data={"test": "data1"},
            severity=5,
            ip_count=10,
            request_count=100
        )
        
        # Creating another pattern with same hash should fail
        with self.assertRaises(IntegrityError):
            AttackPattern.objects.create(
                pattern_hash="0xunique123",
                pattern_data={"test": "data2"},
                severity=7,
                ip_count=20,
                request_count=200
            )
    
    def test_attack_pattern_json_field(self):
        """Test JSON field functionality"""
        complex_data = {
            "attack_type": "DDoS",
            "characteristics": {
                "rate": 200,
                "endpoints": ["/login", "/api/data"],
                "patterns": ["rapid_fire", "endpoint_cycling"]
            },
            "metadata": {
                "detection_confidence": 0.95,
                "false_positive_rate": 0.02
            }
        }
        
        pattern = AttackPattern.objects.create(
            pattern_hash="0xcomplex123",
            pattern_data=complex_data,
            severity=9,
            ip_count=100,
            request_count=20000
        )
        
        # Retrieve and verify JSON data
        retrieved_pattern = AttackPattern.objects.get(pattern_hash="0xcomplex123")
        self.assertEqual(retrieved_pattern.pattern_data, complex_data)
        self.assertEqual(retrieved_pattern.pattern_data["attack_type"], "DDoS")
        self.assertEqual(retrieved_pattern.pattern_data["characteristics"]["rate"], 200)
    
    def test_attack_pattern_with_blockchain_sync(self):
        """Test attack pattern with blockchain synchronization"""
        pattern = AttackPattern.objects.create(
            pattern_hash="0xsynced123",
            pattern_data={"synced": True},
            severity=6,
            ip_count=25,
            request_count=1250,
            blockchain_synced=True,
            signature_tx_hash="0xtxhash456"
        )
        
        self.assertTrue(pattern.blockchain_synced)
        self.assertEqual(pattern.signature_tx_hash, "0xtxhash456")
    
    def test_attack_pattern_str_representation(self):
        """Test string representation of attack pattern"""
        pattern = AttackPattern(
            pattern_hash="0x1234567890abcdef",
            severity=7
        )
        
        expected_str = "Attack pattern 0x123456... (severity 7)"
        self.assertEqual(str(pattern), expected_str)
    
    def test_attack_pattern_ordering(self):
        """Test attack pattern ordering by detected_at (newest first)"""
        old_pattern = AttackPattern.objects.create(
            pattern_hash="0xold123",
            pattern_data={"old": True},
            severity=5,
            ip_count=10,
            request_count=100
        )
        
        new_pattern = AttackPattern.objects.create(
            pattern_hash="0xnew123",
            pattern_data={"new": True},
            severity=8,
            ip_count=50,
            request_count=500
        )
        
        patterns = list(AttackPattern.objects.all())
        self.assertEqual(patterns[0], new_pattern)  # Newest first
        self.assertEqual(patterns[1], old_pattern)
    
    def test_attack_pattern_severity_range(self):
        """Test attack pattern severity values"""
        # Test minimum severity
        min_pattern = AttackPattern.objects.create(
            pattern_hash="0xmin123",
            pattern_data={"severity": "low"},
            severity=1,
            ip_count=5,
            request_count=50
        )
        self.assertEqual(min_pattern.severity, 1)
        
        # Test maximum severity
        max_pattern = AttackPattern.objects.create(
            pattern_hash="0xmax123",
            pattern_data={"severity": "critical"},
            severity=10,
            ip_count=1000,
            request_count=100000
        )
        self.assertEqual(max_pattern.severity, 10)