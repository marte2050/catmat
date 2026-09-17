from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from catmat.api.models import ExpenseNature, Pdm, PdmExpenseNature
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.repository import bulk_insert_ignore, bulk_upsert, existing_codes
from catmat.etl.schemas import ExpenseNatureDTO

logger = logging.getLogger(__name__)


class ExpenseNatureLoader(BaseLoader):
    name = "expense-natures"
    endpoint = "5_consultarMaterialNaturezaDespesa"
    dto_cls = ExpenseNatureDTO
    model = ExpenseNature
    index_elements = ("expense_nature_code",)

    def to_model(self, dto: ExpenseNatureDTO) -> ExpenseNature:
        return ExpenseNature(
            expense_nature_code=dto.expense_nature_code,
            expense_nature_name=dto.expense_nature_name,
            expense_nature_status=dto.expense_nature_status,
        )

    async def process_batch(
        self,
        session: AsyncSession,
        dtos: Sequence[ExpenseNatureDTO],
        *,
        batch_size: int,
    ) -> int:
        natures = {
            dto.expense_nature_code: self.to_model(dto) for dto in dtos
        }
        count = await bulk_upsert(
            session,
            ExpenseNature,
            list(natures.values()),
            index_elements=("expense_nature_code",),
            chunk_size=batch_size,
        )

        pdm_codes = {dto.pdm_code for dto in dtos}
        existing_pdms = await existing_codes(session, Pdm, "pdm_code", pdm_codes)
        missing = pdm_codes - existing_pdms
        if missing:
            logger.warning(
                "[%s] %s PDMs referenciados não existem; associações ignoradas: %s",
                self.name,
                len(missing),
                sorted(missing),
            )

        associations = [
            PdmExpenseNature(
                pdm_code=dto.pdm_code,
                expense_nature_code=dto.expense_nature_code,
            )
            for dto in dtos
            if dto.pdm_code in existing_pdms
        ]
        await bulk_insert_ignore(
            session,
            PdmExpenseNature,
            associations,
            index_elements=("pdm_code", "expense_nature_code"),
            chunk_size=batch_size,
        )
        return count
