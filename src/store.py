from __future__ import annotations

from typing import Any, Callable

from .chunking import compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Uses an in-memory store with deterministic mock embeddings by default.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._store: list[dict[str, Any]] = []
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata) if doc.metadata else {}
        metadata["doc_id"] = doc.id
        embedding = self._embedding_fn(doc.content)
        return {
            "content": doc.content,
            "embedding": embedding,
            "metadata": metadata,
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for record in records:
            score = compute_similarity(query_embedding, record["embedding"])
            result = {
                "content": record["content"],
                "score": score,
                "metadata": record["metadata"],
            }
            scored.append((score, result))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [result for _, result in scored[:top_k]]

    def add_documents(self, docs: list[Document]) -> None:
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        if metadata_filter is None:
            candidates = self._store
        else:
            candidates = [
                r
                for r in self._store
                if all(
                    r.get("metadata", {}).get(k) == v for k, v in metadata_filter.items()
                )
            ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        before = len(self._store)
        self._store = [
            r for r in self._store if r.get("metadata", {}).get("doc_id") != doc_id
        ]
        return len(self._store) < before
