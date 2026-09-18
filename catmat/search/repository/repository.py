from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from catmat.api.models import Class, Group, Item, Pdm


@dataclass(slots=True)
class ItemDetail:
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


async def fetch_items_by_codes(
    session: AsyncSession,
    codes: Sequence[int],
) -> dict[int, ItemDetail]:
    if not codes:
        return {}

    statement = (
        select(
            Item.item_code,
            Item.pdm_code,
            Item.item_description,
            Item.item_status,
            Item.is_sustainable,
            Item.ncm_code,
            Pdm.pdm_name,
            Pdm.class_code,
            Class.class_name,
            Class.group_code,
            Group.group_name,
        )
        .join(Pdm, Item.pdm_code == Pdm.pdm_code)
        .join(Class, Pdm.class_code == Class.class_code)
        .join(Group, Class.group_code == Group.group_code)
        .where(Item.item_code.in_(codes))
    )
    result = await session.execute(statement)

    details: dict[int, ItemDetail] = {}
    for row in result.all():
        details[row.item_code] = ItemDetail(
            item_code=row.item_code,
            pdm_code=row.pdm_code,
            class_code=row.class_code,
            group_code=row.group_code,
            pdm_name=row.pdm_name,
            class_name=row.class_name,
            group_name=row.group_name,
            item_status=row.item_status,
            is_sustainable=row.is_sustainable,
            ncm_code=row.ncm_code,
            item_description=row.item_description,
        )
    return details
