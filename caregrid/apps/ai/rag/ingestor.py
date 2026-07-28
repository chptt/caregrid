import logging
import uuid
from caregrid.apps.ai.models import KnowledgeDocument
from .embeddings import EmbeddingGenerator

logger = logging.getLogger('ai')


class KnowledgeIngestor:
    """Ingests documents into the knowledge base."""

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()

    def ingest_document(self, title: str, content: str, category: str,
                        created_by=None) -> KnowledgeDocument:
        """Add a document to the knowledge base and generate embeddings."""
        doc_id = str(uuid.uuid4())
        doc = KnowledgeDocument.objects.create(
            id=doc_id,
            title=title,
            content=content,
            category=category,
            created_by=created_by,
        )

        metadata = {
            'doc_id': str(doc_id),
            'title': title,
            'category': category,
        }
        embedding_ids = self.embedding_generator.embed_document(doc_id, content, metadata)

        doc.embedding_id = embedding_ids
        doc.save()

        logger.info("Ingested document: %s (%s)", title, category)
        return doc

    def update_document(self, doc_id: str, title: str | None = None,
                        content: str | None = None, category: str | None = None):
        """Update a knowledge base document and regenerate embeddings."""
        try:
            doc = KnowledgeDocument.objects.get(id=doc_id)
        except KnowledgeDocument.DoesNotExist:
            logger.error("Document not found: %s", doc_id)
            return None

        if doc.embedding_id:
            self.embedding_generator.delete_document(str(doc_id))

        if title is not None:
            doc.title = title
        if content is not None:
            doc.content = content
        if category is not None:
            doc.category = category

        metadata = {
            'doc_id': str(doc_id),
            'title': doc.title,
            'category': doc.category,
        }
        embedding_ids = self.embedding_generator.embed_document(
            str(doc_id), doc.content, metadata
        )
        doc.embedding_id = embedding_ids
        doc.save()

        logger.info("Updated document: %s", doc.title)
        return doc

    def delete_document(self, doc_id: str):
        """Remove a document from the knowledge base."""
        try:
            doc = KnowledgeDocument.objects.get(id=doc_id)
        except KnowledgeDocument.DoesNotExist:
            logger.error("Document not found: %s", doc_id)
            return

        if doc.embedding_id:
            self.embedding_generator.delete_document(str(doc_id))

        doc.delete()
        logger.info("Deleted document: %s", doc_id)

    def ingest_text_file(self, file_path: str, title: str, category: str,
                         created_by=None) -> KnowledgeDocument:
        """Ingest a text file into the knowledge base."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.ingest_document(title, content, category, created_by)
