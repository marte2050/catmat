from __future__ import annotations

from catmat.api.models import Group
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.schemas.schemas import GroupDTO


class GroupLoader(BaseLoader):
    name = "groups"
    endpoint = "1_consultarGrupoMaterial"
    dto_cls = GroupDTO
    model = Group
    index_elements = ("group_code",)

    def to_model(self, dto: GroupDTO) -> Group:
        return Group(
            group_code=dto.group_code,
            group_name=dto.group_name,
            group_status=dto.group_status,
            updated_at=dto.updated_at,
        )
