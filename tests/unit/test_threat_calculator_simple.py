"""
Simple unit tests for ThreatScoreCalculator.
"""

from django.test import TestCase, RequestFactory
from unittest.mock import Mock
import redis

from core.threat_calculator import ThreatScoreCalculator


class TestThreatCalculatorSimple(TestCase):
    """Simple unit tests for ThreatScoreCalculator."""
    
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
    
    def test_high_rate_scoring(self):
        """Test high request rate scoring."""
        # Setup high rate scenario
        self.mock_redis.incr.return_value = 150  # Very high rate
        
        score = self.calculator._calculate_rate_score('192.168.1.100')
        
        # Should get maximum rate score
        self.assertEqual(score, 20)
        
        # Verify Redis calls
        self.mock_redis.incr.assert_called_once_with('rate:192.168.1.100')
    
    def test_threat_level_classification(self):
        """Test threat level classification."""
        # Test HIGH threat
        self.assertEqual(self.calculator.get_threat_level(80), 'HIGH')
        self.assertEqual(self.calculator.get_threat_level(61), 'HIGH')
        
        # Test MEDIUM threat
        self.assertEqual(self.calculator.get_threat_level(60), 'MEDIUM')
        self.assertEqual(self.calculator.get_threat_level(50), 'MEDIUM')
        self.assertEqual(self.calculator.get_threat_level(40), 'MEDIUM')
        
        # Test LOW threat
        self.assertEqual(self.calculator.get_threat_level(39), 'LOW')
        self.assertEqual(self.calculator.get_threat_level(20), 'LOW')
        self.assertEqual(self.calculator.get_threat_level(0), 'LOW')