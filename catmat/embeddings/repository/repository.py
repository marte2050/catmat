from __future__ import annotations

from sqlalchemy import bindparam, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from catmat.api.models import Class, Group, Item, Pdm
from catmat.embeddings.schemas import ItemRecord


def _to_record(row) -> ItemRecord:
    return ItemRecord(
        item_code=row.item_code,
        pdm_code=row.pdm_code,
        class_code=row.class_code,
        group_code=row.group_code,
        pdm_name=row.pdm_name,
        class_name=row.class_name,
        group_name=row.group_name,
        item_description=row.item_description,
        item_status=row.item_status,
        is_sustainable=row.is_sustainable,
        ncm_code=row.ncm_code,
        content_hash=row.content_hash,
    )


async def fetch_item_batch(
    session: AsyncSession,
    *,
    after_item_code: int = 0,
    limit: int = 1000,
) -> list[ItemRecord]:
    statement = (
        select(
            Item.item_code,
            Item.pdm_code,
            Item.item_description,
            Item.item_status,
            Item.is_sustainable,
            Item.ncm_code,
            Item.content_hash,
            Pdm.pdm_name,
            Pdm.class_code,
            Class.class_name,
            Class.group_code,
            Group.group_name,
        )
        .join(Pdm, Item.pdm_code == Pdm.pdm_code)
        .join(Class, Pdm.class_code == Class.class_code)
        .join(Group, Class.group_code == Group.group_code)
        .where(Item.item_code > after_item_code)
        .order_by(Item.item_code)
        .limit(limit)
    )
    result = await session.execute(statement)
    return [_to_record(row) for row in result.all()]


async def update_content_hashes(
    session: AsyncSession,
    hashes: dict[int, str],
) -> None:
    if not hashes:
        return

    items = Item.__table__
    statement = (
        update(items)
        .where(items.c.item_code == bindparam("b_item_code"))
        .values(content_hash=bindparam("b_content_hash"))
    )
    await session.execute(
        statement,
        [
            {"b_item_code": item_code, "b_content_hash": digest}
            for item_code, digest in hashes.items()
        ],
    )
