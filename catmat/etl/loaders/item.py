from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from catmat.api.models import Class, Group, Item, Pdm
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.repository import bulk_insert_ignore
from catmat.etl.schemas import ItemDTO


class ItemLoader(BaseLoader):
    name = "items"
    endpoint = "4_consultarItemMaterial"
    dto_cls = ItemDTO
    model = Item
    index_elements = ("item_code",)

    def to_model(self, dto: ItemDTO) -> Item:
        return Item(
            item_code=dto.item_code,
            pdm_code=dto.pdm_code,
            item_description=dto.item_description,
            item_status=dto.item_status,
            is_sustainable=dto.is_sustainable,
            ncm_code=dto.ncm_code,
            ncm_description=dto.ncm_description,
            applies_preference_margin=dto.applies_preference_margin,
            updated_at=dto.updated_at,
        )

    async def process_batch(
        self,
        session: AsyncSession,
        dtos: Sequence[ItemDTO],
        *,
        batch_size: int,
    ) -> int:
        await self._ensure_parents(session, dtos)
        return await super().process_batch(session, dtos, batch_size=batch_size)

    async def _ensure_parents(
        self,
        session: AsyncSession,
        dtos: Sequence[ItemDTO],
    ) -> None:
        """Garante grupos/classes/PDMs referenciados pelos itens (evita violação de FK)."""
        groups = {
            dto.group_code: Group(
                group_code=dto.group_code,
                group_name=dto.group_name,
                group_status=True,
                updated_at=dto.updated_at,
            )
            for dto in dtos
            if dto.group_code is not None and dto.group_name is not None
        }
        classes = {
            dto.class_code: Class(
                class_code=dto.class_code,
                group_code=dto.group_code,
                class_name=dto.class_name,
                class_status=True,
                updated_at=dto.updated_at,
            )
            for dto in dtos
            if dto.class_code is not None
            and dto.class_name is not None
            and dto.group_code is not None
        }
        pdms = {
            dto.pdm_code: Pdm(
                pdm_code=dto.pdm_code,
                class_code=dto.class_code,
                pdm_name=dto.pdm_name,
                pdm_status=True,
                updated_at=dto.updated_at,
            )
            for dto in dtos
            if dto.pdm_name is not None and dto.class_code is not None
        }

        if groups:
            await bulk_insert_ignore(
                session, Group, list(groups.values()), index_elements=("group_code",)
            )
        if classes:
            await bulk_insert_ignore(
                session, Class, list(classes.values()), index_elements=("class_code",)
            )
        if pdms:
            await bulk_insert_ignore(
                session, Pdm, list(pdms.values()), index_elements=("pdm_code",)
            )
