import os
import logging
from .base import OpenAIProvider, GeminiProvider, OllamaProvider, BaseLLMProvider

logger = logging.getLogger('ai')

PROVIDER_MAP: dict[str, type[BaseLLMProvider]] = {
    'openai': OpenAIProvider,
    'gemini': GeminiProvider,
    'ollama': OllamaProvider,
}


def get_llm_provider(provider_name: str | None = None) -> BaseLLMProvider:
    provider_name = (provider_name or os.environ.get('AI_LLM_PROVIDER', 'openai')).lower()
    model_name = os.environ.get('AI_LLM_MODEL', 'gpt-4o-mini')
    api_key = os.environ.get('AI_LLM_API_KEY', '')

    provider_cls = PROVIDER_MAP.get(provider_name)
    if not provider_cls:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Available: {list(PROVIDER_MAP.keys())}")

    kwargs: dict = {}
    if provider_name == 'ollama':
        kwargs['base_url'] = os.environ.get('AI_OLLAMA_BASE_URL', 'http://localhost:11434')

    logger.info("Initializing LLM provider: %s, model: %s", provider_name, model_name)
    return provider_cls(model_name=model_name, api_key=api_key, **kwargs)
