import pytest
import json
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


# Remove SecurityMiddleware from MIDDLEWARE for all tests
@pytest.fixture(autouse=True)
def disable_security_middleware():
    """Disable security middleware for tests to avoid CAPTCHA rate limiting"""
    with override_settings(MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        # 'core.middleware.SecurityMiddleware',  # Disabled for tests
    ]):
        yield


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = User.objects.create_user(username='testdoctor', password='testpass123')
    api_client.force_authenticate(user=user)
    return api_client, user


class TestHealthEndpoint:
    def test_health(self, api_client):
        response = api_client.get('/api/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'CareGrid AI'

    def test_ready(self, api_client):
        response = api_client.get('/api/ready')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ready'


class TestConversationList:
    def test_list_requires_auth(self, api_client):
        response = api_client.get('/api/v1/ai/conversations')
        assert response.status_code == 403

    def test_list_returns_empty(self, authenticated_client):
        client, user = authenticated_client
        response = client.get('/api/v1/ai/conversations')
        assert response.status_code == 200
        data = response.json()
        assert 'conversations' in data
        assert data['conversations'] == []
        assert data['total'] == 0

    def test_list_with_conversation(self, authenticated_client):
        client, user = authenticated_client
        from backend.apps.ai.models import Conversation
        conv = Conversation.objects.create(user=user, agent_type='doctor', title='Test')
        response = client.get('/api/v1/ai/conversations')
        assert response.status_code == 200
        data = response.json()
        assert len(data['conversations']) == 1
        assert data['conversations'][0]['title'] == 'Test'

    def test_list_filter_by_agent_type(self, authenticated_client):
        client, user = authenticated_client
        from backend.apps.ai.models import Conversation
        Conversation.objects.create(user=user, agent_type='doctor', title='Doc')
        Conversation.objects.create(user=user, agent_type='medical_records', title='MR')
        response = client.get('/api/v1/ai/conversations?agent_type=doctor')
        assert response.status_code == 200
        data = response.json()
        assert len(data['conversations']) == 1
        assert data['conversations'][0]['agent_type'] == 'doctor'

    def test_list_pagination(self, authenticated_client):
        client, user = authenticated_client
        from backend.apps.ai.models import Conversation
        for i in range(5):
            Conversation.objects.create(user=user, agent_type='doctor', title=f'Conv {i}')
        response = client.get('/api/v1/ai/conversations?page=1&page_size=2')
        assert response.status_code == 200
        data = response.json()
        assert len(data['conversations']) == 2
        assert data['total'] == 5
        assert data['page'] == 1


class TestUploadDocument:
    def test_requires_auth(self, api_client):
        response = api_client.post('/api/v1/ai/upload-document', {'patient_id': 1})
        assert response.status_code == 403

    def test_missing_patient_id(self, authenticated_client):
        client, user = authenticated_client
        response = client.post('/api/v1/ai/upload-document', {})
        assert response.status_code == 400

    def test_invalid_file_type(self, authenticated_client):
        client, user = authenticated_client
        from core.models import Patient, Branch
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='Test', date_of_birth='1990-01-01', gender='M',
            contact_phone='123', contact_email='t@t.com', branch=branch,
        )
        import io
        f = io.BytesIO(b'fake content')
        f.name = 'test.exe'
        response = client.post('/api/v1/ai/upload-document', {
            'patient_id': patient.id,
            'file': f,
        })
        assert response.status_code == 400


class TestDoctorChat:
    def test_requires_auth(self, api_client):
        response = api_client.post('/api/v1/ai/doctor/chat', {'message': 'Hi'})
        assert response.status_code == 403

    def test_missing_message(self, authenticated_client):
        client, user = authenticated_client
        response = client.post('/api/v1/ai/doctor/chat', {})
        assert response.status_code == 400

    @patch('backend.apps.ai.api.views.DoctorAgent')
    def test_chat_success(self, mock_agent_class, authenticated_client):
        client, user = authenticated_client
        mock_agent = MagicMock()
        mock_agent.chat.return_value = {
            'conversation_id': '00000000-0000-0000-0000-000000000001',
            'response': 'Hello patient',
            'agent_type': 'doctor',
            'tokens_used': 50,
            'explanation': {},
        }
        mock_agent_class.return_value = mock_agent
        response = client.post('/api/v1/ai/doctor/chat', {'message': 'Hello'})
        assert response.status_code == 200
        data = response.json()
        assert data['response'] == 'Hello patient'


class TestMedicalRecordsChat:
    def test_requires_auth(self, api_client):
        response = api_client.post('/api/v1/ai/medical-records/chat', {'document_text': 'text'})
        assert response.status_code == 403

    def test_missing_document_text(self, authenticated_client):
        client, user = authenticated_client
        response = client.post('/api/v1/ai/medical-records/chat', {})
        assert response.status_code == 400

    @patch('backend.apps.ai.api.views.MedicalRecordsAgent')
    def test_chat_extract(self, mock_agent_class, authenticated_client):
        client, user = authenticated_client
        mock_agent = MagicMock()
        mock_agent.extract.return_value = {
            'conversation_id': '00000000-0000-0000-0000-000000000002',
            'response': 'Extracted data',
            'agent_type': 'medical_records',
            'tokens_used': 30,
            'explanation': {},
        }
        mock_agent_class.return_value = mock_agent
        response = client.post('/api/v1/ai/medical-records/chat', {
            'document_text': 'Patient data here',
        })
        assert response.status_code == 200
        data = response.json()
        assert 'response' in data

    @patch('backend.apps.ai.api.views.MedicalRecordsAgent')
    def test_chat_summarize(self, mock_agent_class, authenticated_client):
        client, user = authenticated_client
        mock_agent = MagicMock()
        mock_agent.summarize.return_value = {
            'conversation_id': '00000000-0000-0000-0000-000000000003',
            'response': 'Summary',
            'agent_type': 'medical_records',
            'tokens_used': 20,
            'explanation': {},
        }
        mock_agent_class.return_value = mock_agent
        response = client.post('/api/v1/ai/medical-records/chat', {
            'document_text': 'Data',
            'action': 'summarize',
        })
        assert response.status_code == 200
        data = response.json()
        assert 'response' in data


class TestConversationHistory:
    def test_requires_auth(self, api_client):
        response = api_client.get('/api/v1/ai/history/00000000-0000-0000-0000-000000000001')
        assert response.status_code == 403

    def test_get_history(self, authenticated_client):
        client, user = authenticated_client
        from backend.apps.ai.models import Conversation, Message
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        Message.objects.create(conversation=conv, role='user', content='Hello')
        Message.objects.create(conversation=conv, role='assistant', content='Hi there')
        response = client.get(f'/api/v1/ai/history/{conv.id}')
        assert response.status_code == 200
        data = response.json()
        assert data['agent_type'] == 'doctor'
        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'user'
        assert data['messages'][0]['content'] == 'Hello'

    def test_history_access_denied(self, authenticated_client):
        client, owner = authenticated_client
        other = User.objects.create_user(username='other', password='pass')
        from backend.apps.ai.models import Conversation
        conv = Conversation.objects.create(user=other, agent_type='doctor')
        response = client.get(f'/api/v1/ai/history/{conv.id}')
        assert response.status_code == 403

    def test_history_not_found(self, authenticated_client):
        client, user = authenticated_client
        response = client.get('/api/v1/ai/history/00000000-0000-0000-0000-000000009999')
        assert response.status_code == 404


class TestConversationDelete:
    def test_delete_requires_auth(self, api_client):
        response = api_client.delete('/api/v1/ai/history/00000000-0000-0000-0000-000000000001')
        assert response.status_code == 403

    def test_delete_deactivates(self, authenticated_client):
        client, user = authenticated_client
        from backend.apps.ai.models import Conversation
        conv = Conversation.objects.create(user=user, agent_type='doctor')
        response = client.delete(f'/api/v1/ai/history/{conv.id}')
        assert response.status_code == 200
        conv.refresh_from_db()
        assert conv.is_active is False

    def test_delete_access_denied(self, authenticated_client):
        client, owner = authenticated_client
        other = User.objects.create_user(username='other2', password='pass')
        from backend.apps.ai.models import Conversation
        conv = Conversation.objects.create(user=other, agent_type='doctor')
        response = client.delete(f'/api/v1/ai/history/{conv.id}')
        assert response.status_code == 403

    def test_delete_not_found(self, authenticated_client):
        client, user = authenticated_client
        response = client.delete('/api/v1/ai/history/00000000-0000-0000-0000-000000009999')
        assert response.status_code == 404
