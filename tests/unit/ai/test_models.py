import pytest
from datetime import date
from django.contrib.auth import get_user_model
from core.models import Branch, Patient, Doctor, Appointment
from caregrid.apps.ai.models import (
    Conversation, Message, AISummary, DocumentUpload, KnowledgeDocument,
)

User = get_user_model()


@pytest.fixture
def branch():
    return Branch.objects.create(name='Main', location='City Center')


@pytest.fixture
def user(branch):
    return User.objects.create_user(
        username='testdoc', password='pass123', role='doctor', branch=branch
    )


@pytest.fixture
def patient(branch):
    return Patient.objects.create(
        name='John Doe', date_of_birth=date(1990, 1, 1), gender='Male',
        contact_phone='555-0100', contact_email='john@test.com',
        address='123 Main St', branch=branch,
    )


@pytest.mark.django_db
class TestConversation:
    def test_create(self, user):
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        assert conv.agent_type == 'doctor'
        assert conv.is_active is True
        assert conv.pk is not None

    def test_str(self, user):
        conv = Conversation.objects.create(user=user, agent_type='patient')
        assert 'patient' in str(conv)


@pytest.mark.django_db
class TestMessage:
    def test_create(self, user):
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        msg = Message.objects.create(
            conversation=conv, role='user', content='Hello', tokens_used=5
        )
        assert msg.role == 'user'
        assert msg.tokens_used == 5

    def test_ordering(self, user):
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        m1 = Message.objects.create(conversation=conv, role='user', content='A')
        m2 = Message.objects.create(conversation=conv, role='assistant', content='B')
        msgs = list(conv.messages.all())
        assert msgs[0] == m1
        assert msgs[1] == m2


@pytest.mark.django_db
class TestAISummary:
    def test_create(self, user, patient):
        summary = AISummary.objects.create(
            patient=patient, doctor=user, summary_type='visit',
            content='Test summary',
        )
        assert summary.approved is False
        assert summary.blockchain_hash == ''

    def test_approve(self, user, patient):
        summary = AISummary.objects.create(
            patient=patient, summary_type='history', content='Summary',
        )
        summary.approved = True
        summary.approved_by = user
        summary.save()
        refreshed = AISummary.objects.get(id=summary.id)
        assert refreshed.approved is True
        assert refreshed.approved_by == user


@pytest.mark.django_db
class TestDocumentUpload:
    def test_create(self, user, patient):
        doc = DocumentUpload.objects.create(
            patient=patient, uploaded_by=user,
            original_filename='report.pdf', file_type='pdf',
            file_size=1024,
        )
        assert doc.processing_status == 'pending'

    def test_status_choices(self, user, patient):
        doc = DocumentUpload.objects.create(
            patient=patient, uploaded_by=user,
            original_filename='notes.txt', file_type='txt',
            file_size=512, processing_status='completed',
        )
        assert doc.processing_status == 'completed'


@pytest.mark.django_db
class TestKnowledgeDocument:
    def test_create(self, user):
        doc = KnowledgeDocument.objects.create(
            title='Policy X', category='policy',
            content='Some policy content', created_by=user,
        )
        assert doc.is_active is True
        assert 'policy' in str(doc)

    def test_deactivate(self):
        doc = KnowledgeDocument.objects.create(
            title='Old Doc', category='guideline',
            content='Old content',
        )
        doc.is_active = False
        doc.save()
        assert KnowledgeDocument.objects.filter(is_active=False).count() == 1
