from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catmat.api.models.base import Base

if TYPE_CHECKING:
    from catmat.api.models.classes import Class
    from catmat.api.models.expense_nature import PdmExpenseNature
    from catmat.api.models.item import Item
    from catmat.api.models.supply_unit import SupplyUnit


class Pdm(Base):
    """
        A model PDM (Plano Descritivo de Materiais) representa um plano descritivo de materiais, que é uma estrutura que descreve 
        as caracteríticas dos materiais e faz o agrupamento de catmats. Cada PDM irá possuir um tipo de despesa e terá as unidades
        de fornecimento associadas a ele.
    """
    __tablename__ = "pdms"

    pdm_code: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    class_code: Mapped[int] = mapped_column(
        ForeignKey("classes.class_code", ondelete="CASCADE"), index=True
    )
    pdm_name: Mapped[str] = mapped_column(String(255))
    pdm_status: Mapped[bool] = mapped_column(Boolean)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    item_class: Mapped[Class] = relationship(back_populates="pdms")

    items: Mapped[list[Item]] = relationship(
        back_populates="pdm",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    expense_natures: Mapped[list[PdmExpenseNature]] = relationship(
        back_populates="pdm",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    supply_units: Mapped[list[SupplyUnit]] = relationship(
        back_populates="pdm",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
