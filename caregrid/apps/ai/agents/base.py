import logging
from abc import ABC, abstractmethod
from caregrid.apps.ai.models import Conversation, Message
from caregrid.apps.ai.services.llm_factory import get_llm_provider
from caregrid.apps.ai.memory.conversation_memory import ConversationMemory
from caregrid.apps.ai.prompts.manager import PromptManager

logger = logging.getLogger('ai')


class BaseAgent(ABC):
    """Base class for all AI agents."""

    agent_type: str = 'base'
    description: str = ''

    def __init__(self):
        self.llm = get_llm_provider(self.agent_type)
        self.memory = ConversationMemory()
        self.prompt_manager = PromptManager()

    @abstractmethod
    def get_system_prompt(self, **kwargs) -> str:
        """Return the system prompt for this agent."""

    def chat(self, user_message: str, conversation_id: str | None = None,
             user=None, patient_context=None, **kwargs) -> dict:
        """Process a chat message and return a response."""
        conversation = self._get_or_create_conversation(
            conversation_id=conversation_id,
            user=user,
            patient_context=patient_context,
        )

        history = self.memory.get_context(str(conversation.id), max_messages=20)
        system_prompt = self.get_system_prompt(
            patient_context=patient_context,
            **kwargs,
        )

        messages = [{'role': 'system', 'content': system_prompt}]
        for msg in history:
            messages.append({'role': msg['role'], 'content': msg['content']})
        messages.append({'role': 'user', 'content': user_message})

        try:
            response_text = self.llm.generate(messages, temperature=0.7, max_tokens=2048)
            tokens_used = self.llm.count_tokens(messages)
        except Exception as e:
            logger.error("LLM generation failed for agent %s: %s", self.agent_type, e)
            return {
                'conversation_id': str(conversation.id),
                'response': 'I apologize, but I am unable to process your request at this time. Please try again later.',
                'error': str(e),
            }

        self.memory.add_message(str(conversation.id), 'user', user_message)
        self.memory.add_message(str(conversation.id), 'assistant', response_text)

        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
        )
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response_text,
            tokens_used=tokens_used,
        )

        return {
            'conversation_id': str(conversation.id),
            'response': response_text,
            'agent_type': self.agent_type,
            'tokens_used': tokens_used,
        }

    def _get_or_create_conversation(self, conversation_id, user, patient_context):
        if conversation_id:
            try:
                return Conversation.objects.get(
                    id=conversation_id, user=user, is_active=True
                )
            except Conversation.DoesNotExist:
                logger.warning("Conversation %s not found, creating new", conversation_id)

        return Conversation.objects.create(
            user=user,
            agent_type=self.agent_type,
            patient_context=patient_context,
        )
