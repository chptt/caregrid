import os
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger('ai')


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model_name: str, api_key: str | None = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    def generate(self, messages: list[dict], temperature: float = 0.7,
                 max_tokens: int = 2048, **kwargs) -> str:
        """Generate a response from the LLM."""

    @abstractmethod
    def generate_stream(self, messages: list[dict], temperature: float = 0.7,
                        max_tokens: int = 2048, **kwargs):
        """Generate a streaming response from the LLM."""
        yield

    @abstractmethod
    def count_tokens(self, messages: list[dict]) -> int:
        """Estimate token count for messages."""


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def generate(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def generate_stream(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        stream = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def count_tokens(self, messages):
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            encoding = tiktoken.get_encoding('cl100k_base')
        total = 0
        for msg in messages:
            total += 4
            total += len(encoding.encode(msg.get('content', '')))
        return total


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def generate(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        system_msg = ''
        user_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_msg = msg['content']
            else:
                user_messages.append(msg)
        response = client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            system=system_msg,
            messages=user_messages,
            temperature=temperature,
        )
        return response.content[0].text

    def generate_stream(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        system_msg = ''
        user_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_msg = msg['content']
            else:
                user_messages.append(msg)
        with client.messages.stream(
            model=self.model_name,
            max_tokens=max_tokens,
            system=system_msg,
            messages=user_messages,
            temperature=temperature,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def count_tokens(self, messages):
        total = 0
        for msg in messages:
            total += len(msg.get('content', '')) // 4
        return total


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, model_name, api_key=None, **kwargs):
        super().__init__(model_name, api_key, **kwargs)
        self.base_url = kwargs.get('base_url', 'http://localhost:11434')

    def generate(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        import requests

        payload = {
            'model': self.model_name,
            'messages': messages,
            'stream': False,
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens,
            },
        }
        resp = requests.post(
            f'{self.base_url}/api/chat',
            json=payload,
            timeout=kwargs.get('timeout', 120),
        )
        resp.raise_for_status()
        return resp.json()['message']['content']

    def generate_stream(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        import requests

        payload = {
            'model': self.model_name,
            'messages': messages,
            'stream': True,
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens,
            },
        }
        resp = requests.post(
            f'{self.base_url}/api/chat',
            json=payload,
            stream=True,
            timeout=kwargs.get('timeout', 120),
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                import json
                data = json.loads(line)
                if 'message' in data and 'content' in data['message']:
                    yield data['message']['content']

    def count_tokens(self, messages):
        return sum(len(msg.get('content', '')) // 4 for msg in messages)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider."""

    def generate(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        from openai import AzureOpenAI

        client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.config.get('azure_endpoint', ''),
            api_version=self.config.get('api_version', '2024-02-15-preview'),
        )
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def generate_stream(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        from openai import AzureOpenAI

        client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.config.get('azure_endpoint', ''),
            api_version=self.config.get('api_version', '2024-02-15-preview'),
        )
        stream = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def count_tokens(self, messages):
        return sum(len(msg.get('content', '')) // 4 for msg in messages)


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def generate(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)
        contents = []
        for msg in messages:
            role = 'user' if msg['role'] in ('user', 'system') else 'model'
            contents.append({'role': role, 'parts': [msg['content']]})
        response = model.generate_content(
            contents,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text

    def generate_stream(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)
        contents = []
        for msg in messages:
            role = 'user' if msg['role'] in ('user', 'system') else 'model'
            contents.append({'role': role, 'parts': [msg['content']]})
        response = model.generate_content(
            contents,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
            stream=True,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def count_tokens(self, messages):
        return sum(len(msg.get('content', '')) // 4 for msg in messages)


def get_llm_provider(agent_type: str = 'default') -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    provider_name = os.environ.get('AI_LLM_PROVIDER', 'openai').lower()

    api_key = os.environ.get('AI_LLM_API_KEY', '')
    model_name = os.environ.get('AI_LLM_MODEL', 'gpt-4o-mini')

    provider_map = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'ollama': OllamaProvider,
        'azure': AzureOpenAIProvider,
        'gemini': GeminiProvider,
    }

    provider_cls = provider_map.get(provider_name)
    if not provider_cls:
        raise ValueError(f"Unknown LLM provider: {provider_name}")

    kwargs = {}
    if provider_name == 'azure':
        kwargs['azure_endpoint'] = os.environ.get('AI_AZURE_ENDPOINT', '')
        kwargs['api_version'] = os.environ.get('AI_AZURE_API_VERSION', '2024-02-15-preview')
    elif provider_name == 'ollama':
        kwargs['base_url'] = os.environ.get('AI_OLLAMA_BASE_URL', 'http://localhost:11434')

    logger.info("Initializing LLM provider: %s, model: %s", provider_name, model_name)
    return provider_cls(model_name=model_name, api_key=api_key, **kwargs)
