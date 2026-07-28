import logging
from ..services.embedding_service import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger('ai')


class EmbeddingGenerator:
    """Generates and stores embeddings for documents."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def embed_document(self, doc_id: str, text: str, metadata: dict) -> str:
        """Generate embedding for a document and store it."""
        chunks = self._chunk_text(text)
        stored_ids = []

        for i, chunk in enumerate(chunks):
            embedding = self.embedding_service.embed(chunk)
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_metadata = {
                **metadata,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_text': chunk[:500],
            }
            self.vector_store.add(chunk_id, embedding, chunk_metadata)
            stored_ids.append(chunk_id)

        logger.info("Stored %d chunks for document %s", len(stored_ids), doc_id)
        return ','.join(stored_ids)

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query."""
        return self.embedding_service.embed(query)

    def search(self, query: str, top_k: int = 5, category: str | None = None) -> list[dict]:
        """Search for similar content."""
        query_embedding = self.embed_query(query)
        results = self.vector_store.search(query_embedding, top_k=top_k)

        if category:
            results = [r for r in results if r.get('category') == category]
        return results

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            last_period = chunk.rfind('.')
            if last_period > chunk_size * 0.5:
                end = start + last_period + 1
                chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - overlap

        return [c for c in chunks if c]

    def delete_document(self, doc_id: str):
        """Remove all chunks for a document."""
        metadata = self.vector_store._metadata
        ids_to_remove = [k for k in metadata if k.startswith(f"{doc_id}_chunk_")]
        for chunk_id in ids_to_remove:
            self.vector_store.delete(chunk_id)
        logger.info("Removed %d chunks for document %s", len(ids_to_remove), doc_id)
