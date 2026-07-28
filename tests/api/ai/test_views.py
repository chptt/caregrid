import json
import pytest
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from core.models import Branch, Patient
from caregrid.apps.ai.models import Conversation, Message, AISummary

User = get_user_model()


@pytest.fixture
def branch():
    return Branch.objects.create(name='Test Branch', location='Test Location')


@pytest.fixture
def doctor_user(branch):
    return User.objects.create_user(
        username='doctest', password='pass123', role='doctor', branch=branch
    )


@pytest.fixture
def patient_user(branch):
    return User.objects.create_user(
        username='patienttest', password='pass123', role='patient', branch=branch
    )


@pytest.fixture
def admin_user(branch):
    return User.objects.create_superuser(
        username='admintest', password='pass123', role='admin', branch=branch
    )


@pytest.fixture
def test_patient(branch):
    return Patient.objects.create(
        name='Jane Doe', date_of_birth=date(1985, 5, 15), gender='Female',
        contact_phone='555-0200', contact_email='jane@test.com',
        address='456 Oak Ave', branch=branch,
    )


@pytest.mark.django_db
class TestDoctorChatPermission:
    def test_unauthenticated(self, client):
        resp = client.post(
            reverse('ai:doctor-chat'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        assert resp.status_code in (401, 403, 429)

    def test_patient_denied(self, client, patient_user):
        client.force_login(patient_user)
        resp = client.post(
            reverse('ai:doctor-chat'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        assert resp.status_code in (401, 403)

    def test_invalid_payload(self, client, doctor_user):
        client.force_login(doctor_user)
        resp = client.post(
            reverse('ai:doctor-chat'),
            data=json.dumps({}),
            content_type='application/json',
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestPatientChatPermission:
    def test_unauthenticated(self, client):
        resp = client.post(
            reverse('ai:patient-chat'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        assert resp.status_code in (401, 403, 429)

    def test_doctor_denied(self, client, doctor_user):
        client.force_login(doctor_user)
        resp = client.post(
            reverse('ai:patient-chat'),
            data=json.dumps({'message': 'hello'}),
            content_type='application/json',
        )
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestUploadDocumentPermission:
    def test_unauthenticated(self, client):
        resp = client.post(reverse('ai:records-upload'))
        assert resp.status_code in (401, 403, 429)

    def test_patient_denied(self, client, patient_user):
        client.force_login(patient_user)
        resp = client.post(reverse('ai:records-upload'))
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestKnowledgePermission:
    def test_admin_access(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse('ai:knowledge-list'))
        assert resp.status_code == 200

    def test_doctor_denied(self, client, doctor_user):
        client.force_login(doctor_user)
        resp = client.get(reverse('ai:knowledge-list'))
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestApproveSummaryPermission:
    def test_unauthenticated(self, client):
        resp = client.post(
            reverse('ai:approve-summary', kwargs={'summary_id': '00000000-0000-0000-0000-000000000000'}),
        )
        assert resp.status_code in (401, 403, 429)


@pytest.mark.django_db
class TestConversationHistory:
    def test_not_found(self, client, doctor_user):
        client.force_login(doctor_user)
        resp = client.get(
            reverse('ai:conversation-history', kwargs={'conversation_id': '00000000-0000-0000-0000-000000000000'}),
        )
        assert resp.status_code == 404

    def test_access_own(self, client, doctor_user):
        conv = Conversation.objects.create(user=doctor_user, agent_type='doctor')
        client.force_login(doctor_user)
        resp = client.get(
            reverse('ai:conversation-history', kwargs={'conversation_id': str(conv.id)}),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['agent_type'] == 'doctor'


@pytest.mark.django_db
class TestRAGSearch:
    def test_unauthenticated(self, client):
        resp = client.post(
            reverse('ai:rag-search'),
            data=json.dumps({'query': 'test'}),
            content_type='application/json',
        )
        assert resp.status_code in (401, 403, 429)
