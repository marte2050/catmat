from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable, Sequence
from typing import Any

from qdrant_client import models as qdrant_models

from catmat.core.config import settings
from catmat.core.database import AsyncSessionLocal
from catmat.embeddings.embedder import Embedder
from catmat.embeddings.repository import fetch_item_batch, update_content_hashes
from catmat.embeddings.schemas import ItemRecord
from catmat.embeddings.store import DENSE_VECTOR, SPARSE_VECTOR, QdrantStore
from catmat.embeddings.text import build_item_text, hash_text

logger = logging.getLogger(__name__)


def _chunks(sequence: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for start in range(0, len(sequence), size):
        yield sequence[start : start + size]


class EmbeddingPipeline:
    def __init__(
        self,
        *,
        scan_batch_size: int = 1000,
        embed_batch_size: int | None = None,
        max_items: int | None = None,
        recreate: bool = False,
        embedder: Embedder | None = None,
        store: QdrantStore | None = None,
    ) -> None:
        self.scan_batch_size = scan_batch_size
        self.embed_batch_size = embed_batch_size or settings.embedding_batch_size
        self.max_items = max_items
        self.recreate = recreate
        self._embedder = embedder
        self._store = store

    async def run(self) -> dict[str, int]:
        embedder = self._embedder or Embedder()
        store = self._store or QdrantStore()
        stats = {"scanned": 0, "embedded": 0, "skipped": 0}

        try:
            await store.ensure_collection(recreate=self.recreate)
            last_code = 0

            async with AsyncSessionLocal() as session:
                while True:
                    records = await fetch_item_batch(
                        session,
                        after_item_code=last_code,
                        limit=self.scan_batch_size,
                    )
                    if not records:
                        break

                    if self.max_items is not None:
                        remaining = self.max_items - stats["scanned"]
                        if remaining <= 0:
                            break
                        records = records[:remaining]

                    last_code = records[-1].item_code
                    stats["scanned"] += len(records)
                    await self._process_records(embedder, store, session, records, stats)

                    if self.max_items is not None and stats["scanned"] >= self.max_items:
                        break
        finally:
            await store.close()

        return stats

    async def _process_records(
        self,
        embedder: Embedder,
        store: QdrantStore,
        session,
        records: Sequence[ItemRecord],
        stats: dict[str, int],
    ) -> None:
        pending: list[tuple[ItemRecord, str]] = []
        for record in records:
            text = build_item_text(record)
            digest = hash_text(text)
            if record.content_hash == digest:
                stats["skipped"] += 1
                continue
            pending.append((record, digest))

        for batch in _chunks(pending, self.embed_batch_size):
            records_batch = [record for record, _ in batch]
            texts = [build_item_text(record) for record in records_batch]

            dense_vectors = await asyncio.to_thread(embedder.passage_embed, texts)
            sparse_vectors = await asyncio.to_thread(embedder.sparse_embed, texts)

            points = [
                self._to_point(record, dense, sparse)
                for record, dense, sparse in zip(
                    records_batch, dense_vectors, sparse_vectors
                )
            ]
            await store.upsert(points)
            await update_content_hashes(
                session, {record.item_code: digest for record, digest in batch}
            )
            await session.commit()

            stats["embedded"] += len(batch)
            logger.info("Embedados %s itens (total %s)", len(batch), stats["embedded"])

    @staticmethod
    def _to_point(record: ItemRecord, dense, sparse) -> qdrant_models.PointStruct:
        return qdrant_models.PointStruct(
            id=record.item_code,
            vector={
                DENSE_VECTOR: dense,
                SPARSE_VECTOR: qdrant_models.SparseVector(
                    indices=sparse.indices.tolist(),
                    values=sparse.values.tolist(),
                ),
            },
            payload={
                "item_code": record.item_code,
                "pdm_code": record.pdm_code,
                "class_code": record.class_code,
                "group_code": record.group_code,
                "pdm_name": record.pdm_name,
                "class_name": record.class_name,
                "group_name": record.group_name,
                "item_status": record.item_status,
                "is_sustainable": record.is_sustainable,
                "ncm_code": record.ncm_code,
            },
        )
