import logging
from .embeddings import EmbeddingGenerator

logger = logging.getLogger('ai')


class Retriever:
    """Retrieves relevant context from the knowledge base for RAG."""

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()

    def retrieve(self, query: str, top_k: int = 5, category: str | None = None) -> list[dict]:
        """Retrieve relevant documents for a query."""
        results = self.embedding_generator.search(query, top_k=top_k, category=category)

        formatted = []
        for r in results:
            formatted.append({
                'content': r.get('chunk_text', ''),
                'title': r.get('title', ''),
                'category': r.get('category', ''),
                'score': r.get('score', 0),
                'source': r.get('title', 'Unknown'),
            })

        logger.info("Retrieved %d results for query", len(formatted))
        return formatted

    def build_context(self, query: str, top_k: int = 5, category: str | None = None,
                      max_context_length: int = 4000) -> str:
        """Build a context string from retrieved documents for RAG."""
        results = self.retrieve(query, top_k=top_k, category=category)

        if not results:
            return ""

        context_parts = []
        current_length = 0

        for r in results:
            content = r['content']
            if current_length + len(content) > max_context_length:
                remaining = max_context_length - current_length
                if remaining > 100:
                    content = content[:remaining] + '...'
                    context_parts.append(f"[Source: {r['title']}]\n{content}")
                break

            context_parts.append(f"[Source: {r['title']}]\n{content}")
            current_length += len(content)

        return '\n\n---\n\n'.join(context_parts)
