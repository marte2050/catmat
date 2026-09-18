from __future__ import annotations

import hashlib

from catmat.core.config import settings
from catmat.embeddings.schemas import ItemRecord


def build_item_text(record: ItemRecord, *, max_chars: int | None = None) -> str:
    limit = max_chars if max_chars is not None else settings.embedding_max_chars
    parts = (
        record.group_name,
        record.class_name,
        record.pdm_name,
        record.item_description,
    )
    text = " | ".join(part.strip() for part in parts if part and part.strip())
    return text[:limit]


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
