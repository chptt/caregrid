import pytest
from unittest.mock import patch, MagicMock


pytestmark = pytest.mark.django_db


class TestAuditService:
    def test_log_summary(self):
        from backend.apps.ai.services.audit import AuditService
        from backend.apps.ai.models import AuditTrail
        from django.contrib.auth import get_user_model
        from core.models import Patient, Branch
        User = get_user_model()
        user = User.objects.create_user(username='audit_dr', password='pass')
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='P1', date_of_birth='1990-01-01', gender='M',
            contact_phone='123', contact_email='p1@t.com', branch=branch,
        )
        entry = AuditService.log_summary(
            doctor=user, patient=patient,
            input_text='input', output_text='output',
            ai_model='gpt-4',
        )
        assert isinstance(entry, AuditTrail)
        assert entry.action_type == 'summary'
        assert entry.doctor == user
        assert entry.patient == patient
        assert entry.input_summary == 'input'
        assert entry.output_summary == 'output'
        assert entry.ai_model == 'gpt-4'
        assert entry.blockchain_hash != ''

    def test_log_diagnosis_suggestion(self):
        from backend.apps.ai.services.audit import AuditService
        from backend.apps.ai.models import AuditTrail
        entry = AuditService.log_diagnosis_suggestion(
            doctor=None, patient=None,
            input_text='diag input', output_text='diag output',
        )
        assert entry.action_type == 'diagnosis_suggestion'
        assert entry.input_summary == 'diag input'

    def test_log_test_recommendation(self):
        from backend.apps.ai.services.audit import AuditService
        entry = AuditService.log_test_recommendation(
            doctor=None, patient=None,
            input_text='test input', output_text='test output',
        )
        assert entry.action_type == 'test_recommendation'

    def test_log_extraction(self):
        from backend.apps.ai.services.audit import AuditService
        entry = AuditService.log_extraction(
            doctor=None, patient=None,
            input_text='extract input', output_text='extract output',
        )
        assert entry.action_type == 'record_extraction'

    def test_log_with_conversation_id(self):
        from backend.apps.ai.services.audit import AuditService
        from backend.apps.ai.models import Conversation
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='conv_audit', password='pass')
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        entry = AuditService.log_summary(
            doctor=user, patient=None,
            conversation_id=str(conv.id),
            input_text='in', output_text='out',
        )
        assert entry.conversation == conv

    def test_log_truncates_long_text(self):
        from backend.apps.ai.services.audit import AuditService
        long_text = 'x' * 10000
        entry = AuditService.log_summary(
            doctor=None, patient=None,
            input_text=long_text, output_text=long_text,
        )
        assert len(entry.input_summary) <= 5000
        assert len(entry.output_summary) <= 5000


class TestAISummaryBlockchainService:
    def test_hash_summary_returns_hex_string(self):
        from backend.apps.ai.services.blockchain import AISummaryBlockchainService
        result = AISummaryBlockchainService.hash_summary('test content')
        assert result.startswith('0x')
        assert len(result) == 66
        int(result, 16)

    def test_hash_summary_deterministic(self):
        from backend.apps.ai.services.blockchain import AISummaryBlockchainService
        h1 = AISummaryBlockchainService.hash_summary('same content')
        h2 = AISummaryBlockchainService.hash_summary('same content')
        assert h1 == h2

    def test_hash_summary_different_content(self):
        from backend.apps.ai.services.blockchain import AISummaryBlockchainService
        h1 = AISummaryBlockchainService.hash_summary('content A')
        h2 = AISummaryBlockchainService.hash_summary('content B')
        assert h1 != h2

    def test_verify_hash_valid(self):
        from backend.apps.ai.services.blockchain import AISummaryBlockchainService
        content = 'valid content'
        h = AISummaryBlockchainService.hash_summary(content)
        assert AISummaryBlockchainService.verify_hash('any_id', content, h) is True

    def test_verify_hash_invalid(self):
        from backend.apps.ai.services.blockchain import AISummaryBlockchainService
        content = 'original content'
        h = AISummaryBlockchainService.hash_summary(content)
        assert AISummaryBlockchainService.verify_hash('any_id', 'tampered content', h) is False

    def test_store_hash_returns_dict(self):
        from backend.apps.ai.services.blockchain import AISummaryBlockchainService
        result = AISummaryBlockchainService.store_hash('entity-1', '0xabc123')
        assert result['status'] == 'hash_prepared'
        assert result['entity_id'] == 'entity-1'
        assert result['hash'] == '0xabc123'

    def test_get_audit_entry_hash(self):
        from backend.apps.ai.services.blockchain import AISummaryBlockchainService
        from backend.apps.ai.models import AuditTrail
        entry = AuditTrail.objects.create(action_type='summary')
        h = AISummaryBlockchainService.get_audit_entry_hash(entry)
        assert h.startswith('0x')
        assert len(h) == 66
