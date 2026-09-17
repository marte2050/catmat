from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from catmat.api.models import Pdm, SupplyUnit
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.repository import existing_codes
from catmat.etl.schemas import SupplyUnitDTO

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

    async def process_batch(
        self,
        session: AsyncSession,
        dtos: Sequence[SupplyUnitDTO],
        *,
        batch_size: int,
    ) -> int:
        pdm_codes = {dto.pdm_code for dto in dtos}
        existing_pdms = await existing_codes(session, Pdm, "pdm_code", pdm_codes)
        missing = pdm_codes - existing_pdms
        if missing:
            logger.warning(
                "[%s] %s PDMs referenciados não existem; unidades ignoradas: %s",
                self.name,
                len(missing),
                sorted(missing),
            )

        filtered = [dto for dto in dtos if dto.pdm_code in existing_pdms]
        return await super().process_batch(session, filtered, batch_size=batch_size)
