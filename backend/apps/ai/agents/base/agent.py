import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any

from backend.apps.ai.core.exceptions import AgentError
from backend.apps.ai.providers.factory import get_llm_provider
from backend.apps.ai.providers.base import BaseLLMProvider
from backend.apps.ai.memory.conversation import ConversationMemory
from backend.apps.ai.prompts.manager import PromptManager
from backend.apps.ai.models import Conversation, Message

logger = logging.getLogger('ai')


class BaseAgent(ABC):
    agent_type: str = 'base'
    description: str = ''

    def __init__(self, llm_provider: BaseLLMProvider | None = None):
        self.llm = llm_provider or get_llm_provider()
        self.memory = ConversationMemory()
        self.prompt_manager = PromptManager()

    @abstractmethod
    def get_system_prompt(self, **kwargs) -> str:
        ...

    def chat(self, user_message: str, conversation_id: str | None = None,
             user=None, patient=None, doctor=None, **kwargs) -> dict[str, Any]:
        conversation = self._get_or_create_conversation(
            conversation_id=conversation_id,
            user=user,
            patient=patient,
            doctor=doctor,
        )

        if not conversation.title and len(user_message) > 10:
            conversation.title = user_message[:100]
            conversation.save(update_fields=['title'])

        history = self.memory.get_context(str(conversation.id), max_messages=20)
        system_prompt = self.get_system_prompt(**kwargs)

        messages = [{'role': 'system', 'content': system_prompt}]
        for msg in history:
            messages.append({'role': msg['role'], 'content': msg['content']})
        messages.append({'role': 'user', 'content': user_message})

        try:
            response_text = self.llm.generate(messages, temperature=0.7, max_tokens=2048)
            tokens_used = self.llm.count_tokens(messages)

            self.memory.add_message(str(conversation.id), 'user', user_message)
            self.memory.add_message(str(conversation.id), 'assistant', response_text)

            Message.objects.create(
                conversation=conversation, role='user', content=user_message,
            )
            msg_obj = Message.objects.create(
                conversation=conversation, role='assistant', content=response_text,
                tokens_used=tokens_used,
            )

            return {
                'conversation_id': str(conversation.id),
                'response': response_text,
                'agent_type': self.agent_type,
                'tokens_used': tokens_used,
                'explanation': self._build_explanation(response_text),
            }
        except Exception as e:
            logger.error("LLM generation failed for %s: %s", self.agent_type, e)
            return {
                'conversation_id': str(conversation.id),
                'response': 'I apologize, but I am unable to process your request at this time.',
                'error': str(e),
                'explanation': self._build_explanation(''),
            }

    def _get_or_create_conversation(self, conversation_id, user, patient, doctor):
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
            patient=patient,
            doctor=doctor,
        )

    def _build_explanation(self, response_text: str) -> dict:
        return {
            'reasoning': 'AI analyzed the provided input and generated a response based on available data.',
            'confidence': 'Based on available information',
            'disclaimer': 'AI Suggestion — Requires Doctor Verification',
            'follow_up': 'Review the AI response and verify against clinical knowledge.',
        }
