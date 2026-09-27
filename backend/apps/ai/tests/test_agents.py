import pytest
from unittest.mock import patch, MagicMock, PropertyMock


@pytest.fixture
def mock_audit_service():
    with patch('backend.apps.ai.agents.doctor.agent.AuditService') as m:
        yield m

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_llm_provider():
    mock = MagicMock()
    mock.generate.return_value = 'Mocked AI response'
    mock.count_tokens.return_value = 42
    type(mock).model_name = PropertyMock(return_value='test-model')
    return mock


@pytest.fixture
def mock_get_llm():
    with patch('backend.apps.ai.agents.base.agent.get_llm_provider') as m:
        yield m


class TestBaseAgent:
    def test_chat_returns_expected_keys(self, mock_llm_provider):
        from backend.apps.ai.agents.base.agent import BaseAgent
        
        class ConcreteAgent(BaseAgent):
            def get_system_prompt(self, **kwargs) -> str:
                return 'System prompt'
        
        agent = ConcreteAgent(llm_provider=mock_llm_provider)
        agent.memory = MagicMock()
        agent.memory.get_context.return_value = []
        agent.memory.add_message = MagicMock()
        agent.prompt_manager = MagicMock()
        agent.prompt_manager.get.return_value = 'System prompt'
        agent._get_or_create_conversation = MagicMock()
        
        # Create a real conversation in the DB
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='testuser', password='pass')
        from backend.apps.ai.models import Conversation
        conv = Conversation.objects.create(user=user, agent_type='test', title='Test')
        agent._get_or_create_conversation.return_value = conv
        
        # Mock the _build_explanation
        agent._build_explanation = MagicMock(return_value={'reasoning': 'test'})
        
        # Mock Message.objects.create to avoid FK constraint issues
        with patch('backend.apps.ai.agents.base.agent.Message.objects.create') as mock_msg_create:
            mock_msg_create.return_value = MagicMock()
            result = agent.chat('Hello', user=user, patient=None)
        
        assert 'conversation_id' in result
        assert 'response' in result
        assert result['response'] == 'Mocked AI response'
        assert 'agent_type' in result
        assert 'tokens_used' in result
        assert result['tokens_used'] == 42
        assert 'explanation' in result

    def test_chat_error_returns_fallback(self, mock_llm_provider):
        mock_llm_provider.generate.side_effect = Exception('API down')
        from backend.apps.ai.agents.base.agent import BaseAgent
        
        class ConcreteAgent(BaseAgent):
            def get_system_prompt(self, **kwargs) -> str:
                return 'System prompt'
        
        agent = ConcreteAgent(llm_provider=mock_llm_provider)
        agent.agent_type = 'test'
        agent.memory = MagicMock()
        agent.memory.get_context.return_value = []
        agent.prompt_manager = MagicMock()
        agent.prompt_manager.get.return_value = 'System prompt'
        agent._get_or_create_conversation = MagicMock()
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='testuser2', password='pass')
        from backend.apps.ai.models import Conversation
        conv = Conversation.objects.create(user=user, agent_type='test', title='Test')
        agent._get_or_create_conversation.return_value = conv
        agent._build_explanation = MagicMock(return_value={'reasoning': 'err'})
        
        with patch('backend.apps.ai.agents.base.agent.Message.objects.create') as mock_msg_create:
            mock_msg_create.return_value = MagicMock()
            result = agent.chat('Hello', user=user, patient=None)
        
        assert 'error' in result
        assert 'unable to process' in result['response'].lower()
        assert result['error'] == 'API down'

    def test_get_system_prompt_abstract(self):
        from backend.apps.ai.agents.base.agent import BaseAgent
        with pytest.raises(TypeError):
            BaseAgent()


class TestDoctorAgent:
    def test_initialization(self, mock_llm_provider, mock_audit_service):
        with patch('backend.apps.ai.agents.doctor.agent.RAGPipeline') as mock_rag, \
             patch('backend.apps.ai.providers.factory.get_llm_provider') as mock_get_llm:
            mock_get_llm.return_value = mock_llm_provider
            from backend.apps.ai.agents.doctor.agent import DoctorAgent
            agent = DoctorAgent(llm_provider=mock_llm_provider)
            assert agent.agent_type == 'doctor'
            assert agent.description == 'Clinical decision support with patient data analysis'
            mock_rag.assert_called_once()

    def test_chat_adds_disclaimer(self, mock_llm_provider, mock_audit_service):
        with patch('backend.apps.ai.providers.factory.get_llm_provider') as mock_get_llm, \
             patch('backend.apps.ai.agents.doctor.agent.RAGPipeline') as mock_rag:
            mock_get_llm.return_value = mock_llm_provider
            mock_rag_instance = MagicMock()
            mock_rag_instance.build_context.return_value = 'rag context'
            mock_rag.return_value = mock_rag_instance
            from backend.apps.ai.agents.doctor.agent import DoctorAgent
            agent = DoctorAgent(llm_provider=mock_llm_provider)
            agent.memory = MagicMock()
            agent.memory.get_context.return_value = []
            agent.prompt_manager = MagicMock()
            agent.prompt_manager.get.return_value = 'System prompt'
            agent._get_or_create_conversation = MagicMock()
            conv = MagicMock()
            conv.id = '00000000-0000-0000-0000-000000000003'
            agent._get_or_create_conversation.return_value = conv
            result = agent.chat('Tell me about patient', patient=None)
            assert 'response' in result
            assert 'AI Suggestion' in result['response']
            assert 'Requires Doctor Verification' in result['response']

    def test_summarize_patient_patient_not_found(self, mock_llm_provider, mock_audit_service):
        with patch('backend.apps.ai.providers.factory.get_llm_provider') as mock_get_llm, \
             patch('backend.apps.ai.agents.doctor.agent.RAGPipeline') as mock_rag:
            mock_get_llm.return_value = mock_llm_provider
            from backend.apps.ai.agents.doctor.agent import DoctorAgent
            agent = DoctorAgent(llm_provider=mock_llm_provider)
            result = agent.summarize_patient(patient_id=99999)
            assert 'error' in result
            assert 'Patient not found' in result['error']

    def test_summarize_appointments_patient_not_found(self, mock_llm_provider, mock_audit_service):
        with patch('backend.apps.ai.providers.factory.get_llm_provider') as mock_get_llm, \
             patch('backend.apps.ai.agents.doctor.agent.RAGPipeline') as mock_rag:
            mock_get_llm.return_value = mock_llm_provider
            from backend.apps.ai.agents.doctor.agent import DoctorAgent
            agent = DoctorAgent(llm_provider=mock_llm_provider)
            result = agent.summarize_appointments(patient_id=99999)
            assert 'error' in result
            assert 'Patient not found' in result['error']

    def test_suggest_diagnoses_patient_not_found(self, mock_llm_provider, mock_audit_service):
        with patch('backend.apps.ai.providers.factory.get_llm_provider') as mock_get_llm, \
             patch('backend.apps.ai.agents.doctor.agent.RAGPipeline') as mock_rag:
            mock_get_llm.return_value = mock_llm_provider
            from backend.apps.ai.agents.doctor.agent import DoctorAgent
            agent = DoctorAgent(llm_provider=mock_llm_provider)
            result = agent.suggest_diagnoses(patient_id=99999)
            assert 'error' in result
            assert 'Patient not found' in result['error']


class TestMedicalRecordsAgent:
    def test_initialization(self, mock_llm_provider, mock_audit_service):
        with patch('backend.apps.ai.providers.factory.get_llm_provider') as mock_get_llm:
            mock_get_llm.return_value = mock_llm_provider
            from backend.apps.ai.agents.medical_records.agent import MedicalRecordsAgent
            agent = MedicalRecordsAgent(llm_provider=mock_llm_provider)
            assert agent.agent_type == 'medical_records'
            assert agent.description == 'Extract structured medical data from uploaded records'

    def test_extract_returns_expected_keys(self, mock_llm_provider, mock_audit_service):
        with patch('backend.apps.ai.providers.factory.get_llm_provider') as mock_get_llm:
            mock_get_llm.return_value = mock_llm_provider
            from backend.apps.ai.agents.medical_records.agent import MedicalRecordsAgent
            agent = MedicalRecordsAgent(llm_provider=mock_llm_provider)
            agent.memory = MagicMock()
            agent.memory.get_context.return_value = []
            agent.prompt_manager = MagicMock()
            agent.prompt_manager.get.return_value = 'System prompt with {document_text} and {filename}'
            agent._get_or_create_conversation = MagicMock()
            conv = MagicMock()
            conv.id = '00000000-0000-0000-0000-000000000004'
            agent._get_or_create_conversation.return_value = conv
            result = agent.extract(
                document_text='Patient has fever and cough',
                filename='record.txt',
            )
            assert 'conversation_id' in result
            assert 'response' in result


class TestAgentRegistry:
    def test_register_and_get(self):
        from backend.apps.ai.core.registry import AgentRegistry
        from backend.apps.ai.agents.base.agent import BaseAgent
        class MockAgent(BaseAgent):
            agent_type = 'mock'
            description = 'Mock'
            def get_system_prompt(self, **kwargs):
                return 'prompt'
        AgentRegistry.register('mock_test', MockAgent)
        cls = AgentRegistry.get('mock_test')
        assert cls == MockAgent

    def test_get_nonexistent(self):
        from backend.apps.ai.core.registry import AgentRegistry
        with pytest.raises(KeyError, match='not registered'):
            AgentRegistry.get('nonexistent')

    def test_list(self):
        from backend.apps.ai.core.registry import AgentRegistry
        agents = AgentRegistry.list()
        assert 'doctor' in agents
        assert 'medical_records' in agents

    def test_create(self):
        from backend.apps.ai.core.registry import AgentRegistry
        with patch('backend.apps.ai.agents.doctor.agent.RAGPipeline'):
            agent = AgentRegistry.create('doctor')
            assert agent.agent_type == 'doctor'
