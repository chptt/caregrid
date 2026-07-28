import os
import logging

logger = logging.getLogger('ai')


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self.provider = os.environ.get('AI_EMBEDDING_PROVIDER', 'local')
        self.model_name = os.environ.get('AI_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.dimension = int(os.environ.get('AI_EMBEDDING_DIMENSION', '384'))

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if self.provider == 'openai':
            return self._embed_openai(text)
        return self._embed_local(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if self.provider == 'openai':
            return self._embed_openai_batch(texts)
        return self._embed_local_batch(texts)

    def _embed_local(self, text: str) -> list[float]:
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
            embedding = model.encode(text)
            return embedding.tolist()
        except ImportError:
            logger.warning("sentence-transformers not installed, using hash-based fallback")
            return self._hash_embedding(text)

    def _embed_local_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
            embeddings = model.encode(texts)
            return embeddings.tolist()
        except ImportError:
            logger.warning("sentence-transformers not installed, using hash-based fallback")
            return [self._hash_embedding(t) for t in texts]

    def _embed_openai(self, text: str) -> list[float]:
        from openai import OpenAI

        api_key = os.environ.get('AI_LLM_API_KEY', '')
        model = os.environ.get('AI_OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(input=text, model=model)
        return response.data[0].embedding

    def _embed_openai_batch(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI

        api_key = os.environ.get('AI_LLM_API_KEY', '')
        model = os.environ.get('AI_OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(input=texts, model=model)
        return [item.embedding for item in response.data]

    def _hash_embedding(self, text: str) -> list[float]:
        """Deterministic hash-based embedding as fallback."""
        import hashlib
        import struct

        hash_bytes = hashlib.sha512(text.encode()).digest()
        floats = []
        for i in range(0, min(len(hash_bytes), self.dimension * 4), 4):
            val = struct.unpack('f', hash_bytes[i:i + 4])[0]
            floats.append(val)
        while len(floats) < self.dimension:
            floats.append(0.0)
        return floats[:self.dimension]
