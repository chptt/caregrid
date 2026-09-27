from abc import ABC, abstractmethod
import logging

logger = logging.getLogger('ai')


class BaseLLMProvider(ABC):
    def __init__(self, model_name: str, api_key: str | None = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    def generate(self, messages: list[dict], temperature: float = 0.7,
                 max_tokens: int = 2048, **kwargs) -> str:
        ...

    @abstractmethod
    def count_tokens(self, messages: list[dict]) -> int:
        ...

    @classmethod
    def from_config(cls, **kwargs):
        return cls(**kwargs)


class OpenAIProvider(BaseLLMProvider):
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

    def count_tokens(self, messages):
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            encoding = tiktoken.get_encoding('cl100k_base')
        total = sum(4 + len(encoding.encode(m.get('content', ''))) for m in messages)
        return total


class GeminiProvider(BaseLLMProvider):
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

    def count_tokens(self, messages):
        return sum(len(m.get('content', '')) // 4 for m in messages)


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name, api_key=None, **kwargs):
        super().__init__(model_name, api_key, **kwargs)
        self.base_url = kwargs.get('base_url', 'http://localhost:11434')

    def generate(self, messages, temperature=0.7, max_tokens=2048, **kwargs):
        import requests
        payload = {
            'model': self.model_name,
            'messages': messages,
            'stream': False,
            'options': {'temperature': temperature, 'num_predict': max_tokens},
        }
        resp = requests.post(
            f'{self.base_url}/api/chat', json=payload,
            timeout=kwargs.get('timeout', 120),
        )
        resp.raise_for_status()
        return resp.json()['message']['content']

    def count_tokens(self, messages):
        return sum(len(m.get('content', '')) // 4 for m in messages)
