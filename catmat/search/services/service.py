from __future__ import annotations

from catmat.core.database import AsyncSessionLocal
from catmat.search.repository import fetch_items_by_codes
from catmat.search.retriever import HybridRetriever
from catmat.search.schemas import SearchHit, SearchOutcome, SearchQuery


class SearchService:
    def __init__(self, *, retriever: HybridRetriever) -> None:
        self._retriever = retriever

    async def search(self, request: SearchQuery) -> SearchOutcome:
        points = await self._retriever.search(
            request.query,
            limit=request.limit,
            filters=request.filters,
        )
        codes = [int(point.id) for point in points]

        async with AsyncSessionLocal() as session:
            details = await fetch_items_by_codes(session, codes)

        hits: list[SearchHit] = []
        for point in points:
            detail = details.get(int(point.id))
            if detail is None:
                continue
            hits.append(
                SearchHit(
                    score=point.score,
                    item_code=detail.item_code,
                    pdm_code=detail.pdm_code,
                    class_code=detail.class_code,
                    group_code=detail.group_code,
                    pdm_name=detail.pdm_name,
                    class_name=detail.class_name,
                    group_name=detail.group_name,
                    item_status=detail.item_status,
                    is_sustainable=detail.is_sustainable,
                    ncm_code=detail.ncm_code,
                    item_description=detail.item_description,
                )
            )

        return SearchOutcome(query=request.query, total=len(hits), hits=hits)
