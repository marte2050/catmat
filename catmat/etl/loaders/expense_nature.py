from __future__ import annotations

import logging

from catmat.api.models import ExpenseNature
from catmat.etl.loaders.base import BaseLoader
from catmat.etl.schemas.schemas import ExpenseNatureDTO

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
