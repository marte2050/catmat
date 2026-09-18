from __future__ import annotations

from collections.abc import Sequence

from qdrant_client import AsyncQdrantClient, models

from catmat.core.config import settings

DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"


class QdrantStore:
    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        collection: str | None = None,
        dim: int | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.collection = collection or settings.qdrant_collection_items
        self.dim = dim or settings.embedding_dim
        self._client = AsyncQdrantClient(
            url=url or settings.qdrant_url,
            api_key=api_key or settings.qdrant_api_key,
            timeout=timeout,
        )

    @property
    def client(self) -> AsyncQdrantClient:
        return self._client

    async def close(self) -> None:
        await self._client.close()

    async def ensure_collection(self, *, recreate: bool = False) -> None:
        if recreate and await self._client.collection_exists(self.collection):
            await self._client.delete_collection(self.collection)

        if await self._client.collection_exists(self.collection):
            return

        await self._client.create_collection(
            collection_name=self.collection,
            vectors_config={
                DENSE_VECTOR: models.VectorParams(
                    size=self.dim, distance=models.Distance.COSINE
                )
            },
            sparse_vectors_config={
                SPARSE_VECTOR: models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )
        await self._client.create_payload_index(
            self.collection, "pdm_code", models.PayloadSchemaType.INTEGER
        )
        await self._client.create_payload_index(
            self.collection, "group_code", models.PayloadSchemaType.INTEGER
        )
        await self._client.create_payload_index(
            self.collection, "item_status", models.PayloadSchemaType.BOOL
        )

    async def upsert(self, points: Sequence[models.PointStruct]) -> None:
        if points:
            await self._client.upsert(self.collection, points=list(points), wait=True)

    async def count(self) -> int:
        result = await self._client.count(self.collection, exact=True)
        return result.count

    @staticmethod
    def build_filter(
        *,
        group_code: int | None = None,
        pdm_code: int | None = None,
        only_active: bool = True,
    ) -> models.Filter | None:
        must: list[models.Condition] = []
        if group_code is not None:
            must.append(
                models.FieldCondition(
                    key="group_code", match=models.MatchValue(value=group_code)
                )
            )
        if pdm_code is not None:
            must.append(
                models.FieldCondition(
                    key="pdm_code", match=models.MatchValue(value=pdm_code)
                )
            )
        if only_active:
            must.append(
                models.FieldCondition(
                    key="item_status", match=models.MatchValue(value=True)
                )
            )
        return models.Filter(must=must) if must else None

    async def hybrid_search(
        self,
        *,
        dense: Sequence[float],
        sparse: models.SparseVector,
        limit: int,
        prefetch: int = 100,
        query_filter: models.Filter | None = None,
    ) -> list[models.ScoredPoint]:
        result = await self._client.query_points(
            collection_name=self.collection,
            prefetch=[
                models.Prefetch(
                    query=list(dense), using=DENSE_VECTOR, limit=prefetch
                ),
                models.Prefetch(query=sparse, using=SPARSE_VECTOR, limit=prefetch),
            ],
            query=models.RrfQuery(rrf=models.Rrf()),
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return result.points
