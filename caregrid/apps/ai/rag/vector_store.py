import json
import logging
import uuid
from pathlib import Path

logger = logging.getLogger('ai')


class VectorStore:
    """FAISS-based vector store for document embeddings."""

    def __init__(self, index_path: str | None = None):
        self.index_path = index_path or str(
            Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'vector_store'
        )
        self._index = None
        self._metadata = {}
        self._dimension = int(__import__('os').environ.get('AI_EMBEDDING_DIMENSION', '384'))
        self._load_or_create()

    def _load_or_create(self):
        import numpy as np

        index_file = f'{self.index_path}/faiss.index'
        meta_file = f'{self.index_path}/metadata.json'

        Path(self.index_path).mkdir(parents=True, exist_ok=True)

        if Path(index_file).exists():
            try:
                import faiss

                self._index = faiss.read_index(index_file)
                with open(meta_file, 'r') as f:
                    self._metadata = json.load(f)
                logger.info("Loaded vector store with %d vectors", self._index.ntotal)
                return
            except Exception as e:
                logger.warning("Failed to load vector store: %s", e)

        try:
            import faiss

            self._index = faiss.IndexFlatL2(self._dimension)
        except ImportError:
            logger.warning("faiss not installed, using numpy fallback")
            self._index = NumpyVectorIndex(self._dimension)
        self._metadata = {}

    def add(self, embedding_id: str, vector: list[float], metadata: dict):
        """Add a vector with metadata to the store."""
        import numpy as np

        vector_np = np.array([vector], dtype=np.float32)
        self._index.add(vector_np)
        self._metadata[embedding_id] = metadata
        self._save()

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Search for similar vectors."""
        import numpy as np

        query_np = np.array([query_vector], dtype=np.float32)
        try:
            k = min(top_k, self._index.ntotal)
            if k == 0:
                return []
            distances, indices = self._index.search(query_np, k)
        except Exception as e:
            logger.error("Vector search failed: %s", e)
            return []

        results = []
        all_ids = list(self._metadata.keys())
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(all_ids):
                continue
            embedding_id = all_ids[idx]
            result = self._metadata[embedding_id].copy()
            result['score'] = float(1 / (1 + dist))
            result['embedding_id'] = embedding_id
            results.append(result)
        return results

    def delete(self, embedding_id: str):
        """Remove a vector from the store."""
        if embedding_id in self._metadata:
            del self._metadata[embedding_id]
            self._rebuild_index()
            self._save()

    def count(self) -> int:
        return self._index.ntotal if hasattr(self._index, 'ntotal') else len(self._metadata)

    def _rebuild_index(self):
        """Rebuild the index from remaining metadata."""
        import numpy as np

        if not self._metadata:
            try:
                import faiss
                self._index = faiss.IndexFlatL2(self._dimension)
            except ImportError:
                self._index = NumpyVectorIndex(self._dimension)
            return

        vectors = []
        for mid in self._metadata:
            if 'vector' in self._metadata[mid]:
                vectors.append(self._metadata[mid]['vector'])
        if vectors:
            vectors_np = np.array(vectors, dtype=np.float32)
            try:
                import faiss
                self._index = faiss.IndexFlatL2(self._dimension)
                self._index.add(vectors_np)
            except ImportError:
                self._index = NumpyVectorIndex(self._dimension)
                self._index.vectors = vectors_np

    def _save(self):
        """Persist the index and metadata to disk."""
        try:
            import faiss
            faiss.write_index(self._index, f'{self.index_path}/faiss.index')
        except (ImportError, AttributeError):
            pass
        meta_to_save = {}
        for k, v in self._metadata.items():
            meta_to_save[k] = {mk: mv for mk, mv in v.items() if mk != 'vector'}
        with open(f'{self.index_path}/metadata.json', 'w') as f:
            json.dump(meta_to_save, f, indent=2, default=str)


class NumpyVectorIndex:
    """Fallback vector index using pure numpy."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors = None
        self.ntotal = 0

    def add(self, vectors):
        import numpy as np

        if self.vectors is None:
            self.vectors = vectors
        else:
            self.vectors = np.vstack([self.vectors, vectors])
        self.ntotal = self.vectors.shape[0]

    def search(self, query, k):
        import numpy as np

        if self.vectors is None or self.ntotal == 0:
            return np.array([[]]), np.array([[]])
        distances = np.linalg.norm(self.vectors - query, axis=1)
        k = min(k, self.ntotal)
        top_indices = np.argsort(distances)[:k]
        top_distances = distances[top_indices]
        return np.array([top_distances]), np.array([top_indices])
