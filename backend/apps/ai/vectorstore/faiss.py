import json
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

from .base import BaseVectorStore, SearchResult

logger = logging.getLogger('ai')


class FAISSVectorStore(BaseVectorStore):
    def __init__(self, index_dir: str | None = None):
        self.index_dir = index_dir or str(
            Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'vector_store'
        )
        self._metadata: dict[str, dict] = {}
        self._index = None
        self._dimension = int(os.environ.get('AI_EMBEDDING_DIMENSION', '384'))
        self._load_or_create()

    def _load_or_create(self):
        index_file = f'{self.index_dir}/faiss.index'
        meta_file = f'{self.index_dir}/metadata.json'

        Path(self.index_dir).mkdir(parents=True, exist_ok=True)

        if Path(index_file).exists():
            try:
                import faiss
                self._index = faiss.read_index(index_file)
                with open(meta_file, 'r') as f:
                    self._metadata = json.load(f)
                logger.info("Loaded vector store with %d vectors", self._index.ntotal)
                return
            except Exception as e:
                logger.warning("Failed to load existing index: %s", e)

        import faiss
        self._index = faiss.IndexFlatL2(self._dimension)
        self._metadata = {}

    def add(self, vector_id: str, vector: list[float], metadata: dict | None = None) -> None:
        vector_np = np.array([vector], dtype=np.float32)
        self._index.add(vector_np)
        self._metadata[vector_id] = {
            **(metadata or {}),
            'vector': vector,
        }
        self._save()

    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        query_np = np.array([query_vector], dtype=np.float32)
        k = min(top_k, self._index.ntotal)
        if k == 0:
            return []

        distances, indices = self._index.search(query_np, k)
        all_ids = list(self._metadata.keys())

        results: list[SearchResult] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(all_ids):
                continue
            vector_id = all_ids[idx]
            meta = {k: v for k, v in self._metadata[vector_id].items() if k != 'vector'}
            results.append(SearchResult(
                vector_id=vector_id,
                score=float(1 / (1 + dist)),
                metadata=meta,
                chunk_text=meta.get('chunk_text', ''),
            ))
        return results

    def delete(self, vector_id: str) -> None:
        if vector_id in self._metadata:
            del self._metadata[vector_id]
            self._rebuild_index()
            self._save()

    def count(self) -> int:
        return self._index.ntotal if hasattr(self._index, 'ntotal') else len(self._metadata)

    def _rebuild_index(self):
        import faiss
        if not self._metadata:
            self._index = faiss.IndexFlatL2(self._dimension)
            return
        vectors = []
        for mid in self._metadata:
            if 'vector' in self._metadata[mid]:
                vectors.append(self._metadata[mid]['vector'])
        if vectors:
            vectors_np = np.array(vectors, dtype=np.float32)
            self._index = faiss.IndexFlatL2(self._dimension)
            self._index.add(vectors_np)
        else:
            self._index = faiss.IndexFlatL2(self._dimension)

    def _save(self):
        import faiss
        faiss.write_index(self._index, f'{self.index_dir}/faiss.index')
        meta_to_save = {
            k: {mk: mv for mk, mv in v.items() if mk != 'vector'}
            for k, v in self._metadata.items()
        }
        with open(f'{self.index_dir}/metadata.json', 'w') as f:
            json.dump(meta_to_save, f, indent=2, default=str)
