import json
import logging
from django.core.cache import cache

logger = logging.getLogger('ai')

CACHE_PREFIX = 'ai:conv:'
CACHE_TTL = 60 * 60 * 24


class ConversationMemory:
    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages

    def get_context(self, conversation_id: str, max_messages: int = 20) -> list[dict]:
        cache_key = f'{CACHE_PREFIX}{conversation_id}'
        cached = cache.get(cache_key)
        if cached:
            messages = json.loads(cached) if isinstance(cached, str) else cached
            return messages[-max_messages:]

        from backend.apps.ai.models import Message, Conversation
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
        cache.set(cache_key, json.dumps(result, default=str), CACHE_TTL)
        return result

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        cache_key = f'{CACHE_PREFIX}{conversation_id}'
        cached = cache.get(cache_key)
        messages = json.loads(cached) if cached and isinstance(cached, str) else (cached or [])
        messages.append({'role': role, 'content': content})
        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]
        cache.set(cache_key, json.dumps(messages, default=str), CACHE_TTL)

    def clear(self, conversation_id: str) -> None:
        cache.delete(f'{CACHE_PREFIX}{conversation_id}')
