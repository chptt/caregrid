import logging
from backend.apps.ai.vectorstore.base import BaseVectorStore, SearchResult
from backend.apps.ai.vectorstore.faiss import FAISSVectorStore
from backend.apps.ai.embeddings.base import BaseEmbeddingProvider
from backend.apps.ai.embeddings.openai import OpenAIEmbeddingProvider
from backend.apps.ai.document_processing.chunker import TextChunker, Chunk

logger = logging.getLogger('ai')


class RAGPipeline:
    def __init__(
        self,
        vector_store: BaseVectorStore | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        chunker: TextChunker | None = None,
    ):
        self.vector_store = vector_store or FAISSVectorStore()
        self.embedding_provider = embedding_provider or OpenAIEmbeddingProvider()
        self.chunker = chunker or TextChunker()

    def ingest(self, text: str, source_type: str, source_id: str,
               metadata: dict | None = None) -> list[str]:
        chunks = self.chunker.chunk(text)
        vector_ids: list[str] = []

        for chunk in chunks:
            vector = self.embedding_provider.embed(chunk.text)
            vector_id = f"{source_id}_chunk_{chunk.index}"
            chunk_meta = {
                **(metadata or {}),
                'source_type': source_type,
                'source_id': source_id,
                'chunk_index': chunk.index,
                'chunk_text': chunk.text[:500],
            }
            self.vector_store.add(vector_id, vector, chunk_meta)
            vector_ids.append(vector_id)

        logger.info("Ingested %d chunks for %s/%s", len(chunks), source_type, source_id)
        return vector_ids

    def retrieve(self, query: str, top_k: int = 5,
                 filter_category: str | None = None) -> list[SearchResult]:
        query_vector = self.embedding_provider.embed(query)
        results = self.vector_store.search(query_vector, top_k=top_k)

        if filter_category:
            results = [r for r in results if r.metadata.get('category') == filter_category]
        return results

    def build_context(self, query: str, top_k: int = 5,
                      max_chars: int = 4000) -> str:
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""

        parts: list[str] = []
        length = 0
        for r in results:
            content = r.metadata.get('chunk_text', '')
            if not content:
                continue
            if length + len(content) > max_chars:
                remaining = max_chars - length
                if remaining > 100:
                    parts.append(f"[Source: {r.metadata.get('title', 'Unknown')}]\n{content[:remaining]}...")
                break
            parts.append(f"[Source: {r.metadata.get('title', 'Unknown')}]\n{content}")
            length += len(content)

        return '\n\n---\n\n'.join(parts)
