import pytest
from unittest.mock import MagicMock, patch


class TestRAGPipelineInit:
    def test_default_initialization(self):
        with patch('backend.apps.ai.rag.pipeline.FAISSVectorStore') as mock_vs, \
             patch('backend.apps.ai.rag.pipeline.OpenAIEmbeddingProvider') as mock_emb:
            from backend.apps.ai.rag.pipeline import RAGPipeline
            pipeline = RAGPipeline()
            mock_vs.assert_called_once()
            mock_emb.assert_called_once()

    def test_custom_providers(self):
        from backend.apps.ai.rag.pipeline import RAGPipeline
        mock_store = MagicMock()
        mock_embed = MagicMock()
        from backend.apps.ai.document_processing.chunker import TextChunker
        chunker = TextChunker(chunk_size=500, overlap=50)
        pipeline = RAGPipeline(
            vector_store=mock_store,
            embedding_provider=mock_embed,
            chunker=chunker,
        )
        assert pipeline.vector_store == mock_store
        assert pipeline.embedding_provider == mock_embed
        assert pipeline.chunker == chunker


class TestRAGPipelineRetrieve:
    def test_retrieve_returns_search_results(self):
        from backend.apps.ai.rag.pipeline import RAGPipeline
        from backend.apps.ai.vectorstore.base import SearchResult
        mock_store = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed.return_value = [0.1, 0.2, 0.3]
        mock_store.search.return_value = [
            SearchResult(
                vector_id='v1', score=0.95,
                metadata={'chunk_text': 'result text', 'title': 'Doc1'},
                chunk_text='result text',
            ),
        ]
        pipeline = RAGPipeline(
            vector_store=mock_store,
            embedding_provider=mock_embed,
        )
        results = pipeline.retrieve('test query', top_k=1)
        assert len(results) == 1
        assert results[0].vector_id == 'v1'
        assert results[0].score == 0.95
        mock_embed.embed.assert_called_once_with('test query')
        mock_store.search.assert_called_once_with([0.1, 0.2, 0.3], top_k=1)

    def test_retrieve_with_filter(self):
        from backend.apps.ai.rag.pipeline import RAGPipeline
        from backend.apps.ai.vectorstore.base import SearchResult
        mock_store = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed.return_value = [0.5, 0.5]
        mock_store.search.return_value = [
            SearchResult(vector_id='v1', score=0.9, metadata={'category': 'lab', 'chunk_text': 'a'}, chunk_text='a'),
            SearchResult(vector_id='v2', score=0.8, metadata={'category': 'prescription', 'chunk_text': 'b'}, chunk_text='b'),
        ]
        pipeline = RAGPipeline(vector_store=mock_store, embedding_provider=mock_embed)
        results = pipeline.retrieve('query', top_k=5, filter_category='lab')
        assert len(results) == 1
        assert results[0].vector_id == 'v1'


class TestRAGPipelineBuildContext:
    def test_build_context_returns_string(self):
        from backend.apps.ai.rag.pipeline import RAGPipeline
        from backend.apps.ai.vectorstore.base import SearchResult
        mock_store = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed.return_value = [0.1, 0.2]
        mock_store.search.return_value = [
            SearchResult(
                vector_id='v1', score=0.9,
                metadata={'chunk_text': 'Relevant text content here', 'title': 'MyDoc'},
                chunk_text='Relevant text content here',
            ),
        ]
        pipeline = RAGPipeline(vector_store=mock_store, embedding_provider=mock_embed)
        context = pipeline.build_context('test query', top_k=5, max_chars=4000)
        assert isinstance(context, str)
        assert 'Relevant text content here' in context
        assert 'MyDoc' in context

    def test_build_context_empty_when_no_results(self):
        from backend.apps.ai.rag.pipeline import RAGPipeline
        mock_store = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed.return_value = [0.1, 0.2]
        mock_store.search.return_value = []
        pipeline = RAGPipeline(vector_store=mock_store, embedding_provider=mock_embed)
        context = pipeline.build_context('no results query')
        assert context == ''

    def test_build_context_respects_max_chars(self):
        from backend.apps.ai.rag.pipeline import RAGPipeline
        from backend.apps.ai.vectorstore.base import SearchResult
        mock_store = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed.return_value = [0.1, 0.2]
        long_text = 'x' * 2000
        mock_store.search.return_value = [
            SearchResult(
                vector_id='v1', score=0.9,
                metadata={'chunk_text': long_text, 'title': 'Long'},
                chunk_text=long_text,
            ),
            SearchResult(
                vector_id='v2', score=0.8,
                metadata={'chunk_text': 'second chunk', 'title': 'Short'},
                chunk_text='second chunk',
            ),
        ]
        pipeline = RAGPipeline(vector_store=mock_store, embedding_provider=mock_embed)
        context = pipeline.build_context('query', top_k=5, max_chars=100)
        assert len(context) <= 1000


class TestRAGPipelineIngest:
    def test_ingest_creates_vector_ids(self):
        from backend.apps.ai.rag.pipeline import RAGPipeline
        mock_store = MagicMock()
        mock_embed = MagicMock()
        mock_embed.embed.return_value = [0.5, 0.5, 0.5]
        from backend.apps.ai.document_processing.chunker import TextChunker
        pipeline = RAGPipeline(
            vector_store=mock_store,
            embedding_provider=mock_embed,
            chunker=TextChunker(chunk_size=100, overlap=20),
        )
        text = 'Hello world. ' * 20
        ids = pipeline.ingest(text, source_type='test', source_id='src-1')
        assert len(ids) > 0
        assert all('src-1_chunk_' in vid for vid in ids)
        assert mock_store.add.call_count == len(ids)
