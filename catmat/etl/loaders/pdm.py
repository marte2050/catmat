from __future__ import annotations

from catmat.api.models import Pdm
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.schemas import PdmDTO


class PdmLoader(BaseLoader):
    name = "pdms"
    endpoint = "3_consultarPdmMaterial"
    dto_cls = PdmDTO
    model = Pdm
    index_elements = ("pdm_code",)

    def to_model(self, dto: PdmDTO) -> Pdm:
        return Pdm(
            pdm_code=dto.pdm_code,
            class_code=dto.class_code,
            pdm_name=dto.pdm_name,
            pdm_status=dto.pdm_status,
            updated_at=dto.updated_at,
        )
