from __future__ import annotations

from catmat.api.models import Item
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.schemas.schemas import ItemDTO


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