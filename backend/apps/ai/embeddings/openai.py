import os
from .base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get('AI_OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        self._api_key = os.environ.get('AI_LLM_API_KEY', '')

    def embed(self, text: str) -> list[float]:
        from openai import OpenAI
        client = OpenAI(api_key=self._api_key)
        response = client.embeddings.create(input=text, model=self.model)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI
        client = OpenAI(api_key=self._api_key)
        response = client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]
