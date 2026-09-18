from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ItemRecord:
    item_code: int
    pdm_code: int
    class_code: int
    group_code: int
    pdm_name: str
    class_name: str
    group_name: str
    item_description: str
    item_status: bool
    is_sustainable: bool
    ncm_code: str | None
    content_hash: str | None
