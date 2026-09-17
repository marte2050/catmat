from __future__ import annotations

import logging

from catmat.api.models import SupplyUnit
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.schemas.schemas import SupplyUnitDTO

logger = logging.getLogger(__name__)


class SupplyUnitLoader(BaseLoader):
    name = "supply-units"
    endpoint = "6_consultarMaterialUnidadeFornecimento"
    dto_cls = SupplyUnitDTO
    model = SupplyUnit
    index_elements = ("pdm_code", "supply_unit_sequence")

    def to_model(self, dto: SupplyUnitDTO) -> SupplyUnit:
        return SupplyUnit(
            pdm_code=dto.pdm_code,
            supply_unit_sequence=dto.supply_unit_sequence,
            supply_unit_acronym=dto.supply_unit_acronym,
            supply_unit_name=dto.supply_unit_name,
            supply_unit_description=dto.supply_unit_description,
            measure_unit_acronym=dto.measure_unit_acronym,
            measure_unit_capacity=dto.measure_unit_capacity,
            supply_unit_pdm_status=dto.supply_unit_pdm_status,
            supply_unit_status=dto.supply_unit_status,
            supply_unit_updated_at=dto.supply_unit_updated_at,
        )