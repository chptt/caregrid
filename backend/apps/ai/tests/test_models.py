import pytest
from datetime import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


pytestmark = pytest.mark.django_db


class TestAuditTrail:
    def test_create_audit_trail(self):
        from backend.apps.ai.models import AuditTrail
        entry = AuditTrail.objects.create(
            action_type='summary',
            ai_model='gpt-4',
            input_summary='test input',
            output_summary='test output',
        )
        assert entry.action_type == 'summary'
        assert entry.ai_model == 'gpt-4'
        assert entry.input_summary == 'test input'
        assert entry.output_summary == 'test output'
        assert entry.id is not None
        assert entry.blockchain_hash == ''
        assert entry.confidence_score is None

    def test_str_method(self):
        from backend.apps.ai.models import AuditTrail
        user = User.objects.create_user(username='dr_test', password='pass')
        entry = AuditTrail.objects.create(
            action_type='diagnosis_suggestion',
            doctor=user,
        )
        expected = f"diagnosis_suggestion by {user} at {entry.created_at.isoformat()}"
        assert str(entry) == expected

    def test_default_ordering(self):
        from backend.apps.ai.models import AuditTrail
        e1 = AuditTrail.objects.create(action_type='summary', created_at=timezone.make_aware(datetime(2024, 1, 1)))
        e2 = AuditTrail.objects.create(action_type='summary', created_at=timezone.make_aware(datetime(2024, 6, 1)))
        qs = AuditTrail.objects.all()
        assert list(qs) == [e2, e1]


class TestConversation:
    def test_create_conversation(self):
        from backend.apps.ai.models import Conversation
        user = User.objects.create_user(username='conv_user', password='pass')
        conv = Conversation.objects.create(
            user=user,
            agent_type='doctor',
            title='Test Conversation',
        )
        assert conv.agent_type == 'doctor'
        assert conv.title == 'Test Conversation'
        assert conv.is_active is True
        assert conv.id is not None

    def test_str_method(self):
        from backend.apps.ai.models import Conversation
        user = User.objects.create_user(username='str_user', password='pass')
        conv = Conversation.objects.create(user=user, agent_type='medical_records')
        assert str(conv) == f"medical_records conversation {conv.id}"

    def test_agent_type_choices(self):
        from backend.apps.ai.models import Conversation
        user = User.objects.create_user(username='choice_user', password='pass')
        for agent in ('doctor', 'medical_records'):
            conv = Conversation.objects.create(user=user, agent_type=agent)
            assert conv.agent_type == agent


class TestMessage:
    def test_create_message(self):
        from backend.apps.ai.models import Conversation, Message
        user = User.objects.create_user(username='msg_user', password='pass')
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        msg = Message.objects.create(
            conversation=conv,
            role='user',
            content='Hello',
            tokens_used=5,
        )
        assert msg.role == 'user'
        assert msg.content == 'Hello'
        assert msg.tokens_used == 5
        assert msg.conversation == conv

    def test_str_method(self):
        from backend.apps.ai.models import Conversation, Message
        user = User.objects.create_user(username='msg_str', password='pass')
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        msg = Message.objects.create(conversation=conv, role='assistant', content='Hi')
        assert str(msg) == f"assistant in {conv.id}"

    def test_message_ordering(self):
        from backend.apps.ai.models import Conversation, Message
        user = User.objects.create_user(username='ord_user', password='pass')
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        m1 = Message.objects.create(conversation=conv, role='user', content='First')
        m2 = Message.objects.create(conversation=conv, role='assistant', content='Second')
        qs = Message.objects.filter(conversation=conv)
        assert list(qs) == [m1, m2]


class TestUploadedDocument:
    def test_create_document(self):
        from backend.apps.ai.models import UploadedDocument
        from core.models import Patient, Branch
        user = User.objects.create_user(username='doc_user', password='pass')
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='John', date_of_birth='1990-01-01', gender='M',
            contact_phone='123', contact_email='j@t.com', branch=branch,
        )
        doc = UploadedDocument.objects.create(
            patient=patient,
            uploaded_by=user,
            original_filename='test.txt',
            file_type='txt',
            file_size=1024,
        )
        assert doc.original_filename == 'test.txt'
        assert doc.file_type == 'txt'
        assert doc.file_size == 1024
        assert doc.processing_status == 'pending'

    def test_str_method(self):
        from backend.apps.ai.models import UploadedDocument
        from core.models import Patient, Branch
        user = User.objects.create_user(username='doc_str', password='pass')
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='Jane', date_of_birth='1990-01-01', gender='F',
            contact_phone='123', contact_email='j@t.com', branch=branch,
        )
        doc = UploadedDocument.objects.create(
            patient=patient, uploaded_by=user,
            original_filename='report.txt', file_type='txt', file_size=512,
        )
        assert str(doc) == 'report.txt (pending)'


class TestAISummary:
    def test_create_summary(self):
        from backend.apps.ai.models import AISummary
        from core.models import Patient, Branch
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='Joe', date_of_birth='1985-05-05', gender='M',
            contact_phone='123', contact_email='j@t.com', branch=branch,
        )
        summary = AISummary.objects.create(
            patient=patient,
            summary_type='patient_history',
            content='Summary content here',
        )
        assert summary.summary_type == 'patient_history'
        assert summary.content == 'Summary content here'
        assert summary.approved is False
        assert summary.blockchain_hash == ''

    def test_str_method(self):
        from backend.apps.ai.models import AISummary
        from core.models import Patient, Branch
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='Alice', date_of_birth='1992-03-03', gender='F',
            contact_phone='123', contact_email='a@t.com', branch=branch,
        )
        summary = AISummary.objects.create(
            patient=patient,
            summary_type='prescriptions',
            content='Rx summary',
        )
        assert str(summary) == f"prescriptions summary for {patient}"


class TestEmbeddingMetadata:
    def test_create_embedding(self):
        from backend.apps.ai.models import EmbeddingMetadata
        emb = EmbeddingMetadata.objects.create(
            source_type='document',
            source_id='src-123',
            chunk_index=0,
            chunk_text='Some text chunk',
            embedding_model='test-model',
            vector_id='vec-001',
        )
        assert emb.source_type == 'document'
        assert emb.chunk_text == 'Some text chunk'
        assert emb.vector_id == 'vec-001'

    def test_str_method(self):
        from backend.apps.ai.models import EmbeddingMetadata
        emb = EmbeddingMetadata.objects.create(
            source_type='document',
            chunk_text='text',
            vector_id='vec-abc',
        )
        assert str(emb) == 'Embedding vec-abc for document'


class TestRelationships:
    def test_conversation_message_relationship(self):
        from backend.apps.ai.models import Conversation, Message
        user = User.objects.create_user(username='rel_user', password='pass')
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        msg1 = Message.objects.create(conversation=conv, role='user', content='Q')
        msg2 = Message.objects.create(conversation=conv, role='assistant', content='A')
        assert list(conv.messages.all()) == [msg1, msg2]
        assert msg1.conversation == conv
        assert msg2.conversation == conv

    def test_document_embedding_relationship(self):
        from backend.apps.ai.models import UploadedDocument, EmbeddingMetadata
        from core.models import Patient, Branch
        user = User.objects.create_user(username='emb_rel', password='pass')
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='Bob', date_of_birth='1980-01-01', gender='M',
            contact_phone='123', contact_email='b@t.com', branch=branch,
        )
        doc = UploadedDocument.objects.create(
            patient=patient, uploaded_by=user,
            original_filename='doc.txt', file_type='txt', file_size=100,
        )
        emb = EmbeddingMetadata.objects.create(
            document=doc,
            chunk_text='chunk',
            vector_id='v1',
        )
        assert emb.document == doc
        assert list(doc.embeddings.all()) == [emb]

    def test_conversation_aisummary_relationship(self):
        from backend.apps.ai.models import Conversation, AISummary
        from core.models import Patient, Branch
        user = User.objects.create_user(username='sum_rel', password='pass')
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='Carol', date_of_birth='1995-01-01', gender='F',
            contact_phone='123', contact_email='c@t.com', branch=branch,
        )
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        summary = AISummary.objects.create(
            patient=patient,
            summary_type='findings',
            content='findings',
            source_conversation=conv,
        )
        assert summary.source_conversation == conv
        assert list(conv.summaries.all()) == [summary]
