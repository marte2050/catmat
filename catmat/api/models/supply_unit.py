from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catmat.core.base import Base

if TYPE_CHECKING:
    from catmat.api.models.pdm import Pdm


class SupplyUnit(Base):
    """Unidades de fornecimento associadas a um PDM."""

    __tablename__ = "supply_units"

    pdm_code: Mapped[int] = mapped_column(
        ForeignKey("pdms.pdm_code", ondelete="CASCADE"), primary_key=True
    )
    supply_unit_sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    supply_unit_acronym: Mapped[str | None] = mapped_column(String(50))
    supply_unit_name: Mapped[str | None] = mapped_column(String(255))
    supply_unit_description: Mapped[str | None] = mapped_column(Text)
    measure_unit_acronym: Mapped[str | None] = mapped_column(String(20))
    measure_unit_capacity: Mapped[str | None] = mapped_column(String(50))
    supply_unit_pdm_status: Mapped[bool | None] = mapped_column(Boolean)
    supply_unit_status: Mapped[bool | None] = mapped_column(Boolean)
    supply_unit_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False)
    )

    pdm: Mapped[Pdm] = relationship(back_populates="supply_units")
