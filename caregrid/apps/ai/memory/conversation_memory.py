import json
import logging
from django.core.cache import cache

logger = logging.getLogger('ai')

MEMORY_CACHE_PREFIX = 'ai:conv:'
MEMORY_TTL = 60 * 60 * 24  # 24 hours


class ConversationMemory:
    """Manages conversation context using Redis/Django cache."""

    def __init__(self):
        self.max_messages = 50

    def get_context(self, conversation_id: str, max_messages: int = 20) -> list[dict]:
        """Retrieve conversation history."""
        cache_key = f'{MEMORY_CACHE_PREFIX}{conversation_id}'
        cached = cache.get(cache_key)
        if cached:
            messages = json.loads(cached) if isinstance(cached, str) else cached
            return messages[-max_messages:]

        from caregrid.apps.ai.models import Message, Conversation

        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return []

        messages = list(
            Message.objects.filter(conversation=conversation)
            .order_by('-created_at')[:max_messages]
            .values_list('role', 'content')
        )
        messages.reverse()
        result = [{'role': role, 'content': content} for role, content in messages]

        cache.set(cache_key, json.dumps(result, default=str), MEMORY_TTL)
        return result

    def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation context."""
        cache_key = f'{MEMORY_CACHE_PREFIX}{conversation_id}'
        cached = cache.get(cache_key)
        messages = json.loads(cached) if cached and isinstance(cached, str) else (cached or [])

        messages.append({'role': role, 'content': content})

        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]

        cache.set(cache_key, json.dumps(messages, default=str), MEMORY_TTL)

    def clear(self, conversation_id: str):
        """Clear conversation context."""
        cache_key = f'{MEMORY_CACHE_PREFIX}{conversation_id}'
        cache.delete(cache_key)

    def get_token_estimate(self, conversation_id: str) -> int:
        """Estimate total tokens in conversation context."""
        messages = self.get_context(conversation_id, max_messages=self.max_messages)
        return sum(len(msg.get('content', '')) // 4 for msg in messages)
