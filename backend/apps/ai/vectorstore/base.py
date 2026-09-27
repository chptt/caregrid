from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    vector_id: str
    score: float
    metadata: dict
    chunk_text: str


class BaseVectorStore(ABC):
    @abstractmethod
    def add(self, vector_id: str, vector: list[float], metadata: dict | None = None) -> None:
        ...

    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]:
        ...

    @abstractmethod
    def delete(self, vector_id: str) -> None:
        ...

    @abstractmethod
    def count(self) -> int:
        ...
