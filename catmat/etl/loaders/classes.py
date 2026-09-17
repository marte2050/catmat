from __future__ import annotations

from catmat.api.models import Class
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.schemas import ClassDTO


class ClassLoader(BaseLoader):
    name = "classes"
    endpoint = "2_consultarClasseMaterial"
    dto_cls = ClassDTO
    model = Class
    index_elements = ("class_code",)

    def to_model(self, dto: ClassDTO) -> Class:
        return Class(
            class_code=dto.class_code,
            group_code=dto.group_code,
            class_name=dto.class_name,
            class_status=dto.class_status,
            updated_at=dto.updated_at,
        )
