"""
Shared pytest fixtures for MediChain tests
"""

import pytest
from django.conf import settings
import fakeredis
from web3 import Web3
from eth_tester import EthereumTester


@pytest.fixture
def redis_client():
    """Provide a fake Redis client for testing"""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture(scope="session")
def test_blockchain():
    """Provide a test blockchain instance using eth-tester"""
    tester = EthereumTester()
    w3 = Web3(Web3.EthereumTesterProvider(tester))
    return w3


@pytest.fixture
def test_account(test_blockchain):
    """Provide a test account with ETH"""
    return test_blockchain.eth.accounts[0]


@pytest.fixture
def blockchain_service(test_blockchain, test_account):
    """Provide a blockchain service instance for testing"""
    # This will be implemented when BlockchainService is created
    # For now, return a mock
    class MockBlockchainService:
        def __init__(self):
            self.w3 = test_blockchain
            self.account = test_account
        
        def register_patient(self, patient_id_hash):
            return "0x" + "0" * 64, True
        
        def is_patient_registered(self, patient_id_hash):
            return True
        
        def block_ip(self, ip_hash, duration, reason):
            return "0x" + "0" * 64, True
        
        def is_ip_blocked(self, ip_hash):
            return False
        
        def unblock_ip(self, ip_hash):
            return "0x" + "0" * 64, True
        
        def add_attack_signature(self, pattern_json, severity):
            return "0x" + "0" * 64, True
        
        def get_attack_signatures(self):
            return []
    
    return MockBlockchainService()


@pytest.fixture
def db_with_branches(db):
    """Create test branches in the database"""
    from core.models import Branch
    
    branch_a = Branch.objects.create(
        name="Branch A",
        location="Location A"
    )
    branch_b = Branch.objects.create(
        name="Branch B",
        location="Location B"
    )
    
    return {
        'branch_a': branch_a,
        'branch_b': branch_b
    }


@pytest.fixture
def sample_patient_data():
    """Provide sample patient data for testing"""
    from datetime import date
    
    return {
        'name': 'John Doe',
        'date_of_birth': date(1990, 1, 1),
        'gender': 'M',
        'contact_email': 'john.doe@example.com',
        'contact_phone': '+1234567890',
        'address': '123 Main St, City, State 12345'
    }


@pytest.fixture
def threat_calculator(redis_client, blockchain_service):
    """Provide a ThreatScoreCalculator instance for testing"""
    # This will be implemented when ThreatScoreCalculator is created
    # For now, return None
    return None


@pytest.fixture
def mock_request():
    """Provide a mock Django request object"""
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    
    factory = RequestFactory()
    request = factory.get('/api/test/')
    request.user = AnonymousUser()
    request.session = {}
    
    return request
