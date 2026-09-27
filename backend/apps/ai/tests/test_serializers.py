import pytest
import io
from unittest.mock import MagicMock


class TestChatRequestSerializer:
    def test_valid_message(self):
        from backend.apps.ai.serializers.chat import ChatRequestSerializer
        serializer = ChatRequestSerializer(data={'message': 'Hello'})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['message'] == 'Hello'

    def test_empty_message_invalid(self):
        from backend.apps.ai.serializers.chat import ChatRequestSerializer
        serializer = ChatRequestSerializer(data={'message': ''})
        assert not serializer.is_valid()
        assert 'message' in serializer.errors

    def test_message_too_long(self):
        from backend.apps.ai.serializers.chat import ChatRequestSerializer
        serializer = ChatRequestSerializer(data={'message': 'x' * 10001})
        assert not serializer.is_valid()
        assert 'message' in serializer.errors

    def test_missing_message(self):
        from backend.apps.ai.serializers.chat import ChatRequestSerializer
        serializer = ChatRequestSerializer(data={})
        assert not serializer.is_valid()
        assert 'message' in serializer.errors

    def test_with_optional_conversation_id(self):
        from backend.apps.ai.serializers.chat import ChatRequestSerializer
        data = {'message': 'Hi', 'conversation_id': '00000000-0000-0000-0000-000000000001'}
        serializer = ChatRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert str(serializer.validated_data['conversation_id']) == '00000000-0000-0000-0000-000000000001'

    def test_with_optional_patient_id(self):
        from backend.apps.ai.serializers.chat import ChatRequestSerializer
        data = {'message': 'Hi', 'patient_id': 42}
        serializer = ChatRequestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['patient_id'] == 42

    def test_invalid_uuid(self):
        from backend.apps.ai.serializers.chat import ChatRequestSerializer
        data = {'message': 'Hi', 'conversation_id': 'not-a-uuid'}
        serializer = ChatRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'conversation_id' in serializer.errors


class TestUploadDocumentSerializer:
    def test_valid(self):
        from backend.apps.ai.serializers.document import UploadDocumentSerializer
        f = io.BytesIO(b'file content')
        f.name = 'test.txt'
        data = {'patient_id': 1, 'file': f}
        serializer = UploadDocumentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['patient_id'] == 1
        assert serializer.validated_data['file'] is not None

    def test_missing_patient_id(self):
        from backend.apps.ai.serializers.document import UploadDocumentSerializer
        f = io.BytesIO(b'content')
        f.name = 't.txt'
        serializer = UploadDocumentSerializer(data={'file': f})
        assert not serializer.is_valid()
        assert 'patient_id' in serializer.errors

    def test_missing_file(self):
        from backend.apps.ai.serializers.document import UploadDocumentSerializer
        serializer = UploadDocumentSerializer(data={'patient_id': 1})
        assert not serializer.is_valid()
        assert 'file' in serializer.errors


class TestConversationListSerializer:
    def test_serialization(self):
        from backend.apps.ai.serializers.conversation import ConversationListSerializer
        from backend.apps.ai.models import Conversation
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='ser_user', password='pass')
        conv = Conversation.objects.create(user=user, agent_type='doctor', title='Test Conv')
        serializer = ConversationListSerializer(conv)
        data = serializer.data
        assert data['title'] == 'Test Conv'
        assert data['agent_type'] == 'doctor'
        assert data['is_active'] is True
        assert data['message_count'] == 0
        assert 'id' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_serialization_with_patient(self):
        from backend.apps.ai.serializers.conversation import ConversationListSerializer
        from backend.apps.ai.models import Conversation
        from django.contrib.auth import get_user_model
        from core.models import Patient, Branch
        User = get_user_model()
        user = User.objects.create_user(username='ser_user2', password='pass')
        branch = Branch.objects.create(name='Main', location='City')
        patient = Patient.objects.create(
            name='Alice Smith', date_of_birth='1990-01-01', gender='F',
            contact_phone='123', contact_email='a@t.com', branch=branch,
        )
        conv = Conversation.objects.create(
            user=user, agent_type='doctor', title='Test', patient=patient,
        )
        serializer = ConversationListSerializer(conv)
        data = serializer.data
        assert data['patient_name'] == 'Alice Smith'
        assert data['patient_id'] == patient.id

    def test_multiple_serialization(self):
        from backend.apps.ai.serializers.conversation import ConversationListSerializer
        from backend.apps.ai.models import Conversation
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='ser_user3', password='pass')
        convs = [
            Conversation.objects.create(user=user, agent_type='doctor', title='A'),
            Conversation.objects.create(user=user, agent_type='medical_records', title='B'),
        ]
        serializer = ConversationListSerializer(convs, many=True)
        data = serializer.data
        assert len(data) == 2
        assert data[0]['title'] == 'A'
        assert data[1]['title'] == 'B'
