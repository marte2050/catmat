from __future__ import annotations

import asyncio

from qdrant_client import models

from catmat.embeddings.embedder import Embedder
from catmat.embeddings.store import QdrantStore
from catmat.search.schemas import SearchFilters


class HybridRetriever:
    def __init__(
        self,
        *,
        embedder: Embedder,
        store: QdrantStore,
        prefetch: int = 100,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self.prefetch = prefetch

    async def search(
        self,
        query: str,
        *,
        limit: int,
        filters: SearchFilters,
    ) -> list[models.ScoredPoint]:
        dense, sparse = await asyncio.to_thread(self._embed_query, query)
        query_filter = self._store.build_filter(
            group_code=filters.group_code,
            pdm_code=filters.pdm_code,
            only_active=filters.only_active,
        )
        return await self._store.hybrid_search(
            dense=dense,
            sparse=sparse,
            limit=limit,
            prefetch=self.prefetch,
            query_filter=query_filter,
        )

    def _embed_query(self, query: str) -> tuple[list[float], models.SparseVector]:
        dense = self._embedder.query_embed([query])[0]
        sparse_embedding = self._embedder.sparse_embed([query])[0]
        sparse = models.SparseVector(
            indices=sparse_embedding.indices.tolist(),
            values=sparse_embedding.values.tolist(),
        )
        return dense, sparse
