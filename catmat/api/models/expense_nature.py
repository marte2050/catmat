from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catmat.core.base import Base

if TYPE_CHECKING:
    from catmat.api.models.pdm import Pdm


class ExpenseNature(Base):
    """
        Esse tabela é responsável por definir as naturezas de despesas que podem ser associadas aos PDMS cadastrados no sistema. 
        Cada natureza de despesa possui um código único, um nome descritivo e um status que indica se a natureza de despesa está ativa 
        ou inativa.
    """

    __tablename__ = "expense_natures"

    expense_nature_code: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    expense_nature_name: Mapped[str] = mapped_column(String(255))
    expense_nature_status: Mapped[bool] = mapped_column(Boolean)

    pdms: Mapped[list[PdmExpenseNature]] = relationship(
        back_populates="expense_nature",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PdmExpenseNature(Base):
    __tablename__ = "pdm_expense_natures"

    pdm_code: Mapped[int] = mapped_column(
        ForeignKey("pdms.pdm_code", ondelete="CASCADE"), primary_key=True
    )
    expense_nature_code: Mapped[int] = mapped_column(
        ForeignKey("expense_natures.expense_nature_code", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    pdm: Mapped[Pdm] = relationship(back_populates="expense_natures")
    expense_nature: Mapped[ExpenseNature] = relationship(back_populates="pdms")
