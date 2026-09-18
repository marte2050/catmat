from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SearchFilters:
    group_code: int | None = None
    pdm_code: int | None = None
    only_active: bool = True


@dataclass(slots=True)
class SearchQuery:
    query: str
    limit: int = 10
    filters: SearchFilters = field(default_factory=SearchFilters)


@dataclass(slots=True)
class SearchHit:
    score: float
    item_code: int
    pdm_code: int
    class_code: int
    group_code: int
    pdm_name: str
    class_name: str
    group_name: str
    item_status: bool
    is_sustainable: bool
    ncm_code: str | None
    item_description: str


@dataclass(slots=True)
class SearchOutcome:
    query: str
    total: int
    hits: list[SearchHit]
