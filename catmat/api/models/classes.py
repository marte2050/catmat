from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catmat.api.models.base import Base

if TYPE_CHECKING:
    from catmat.api.models.group import Group
    from catmat.api.models.pdm import Pdm


class Class(Base):
    """
        Representam a tabela de classes do Catmat, que contém informações sobre as classes de materiais cadastradas no sistema no
        comprasnet.
    """
    __tablename__ = "classes"

    class_code: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    group_code: Mapped[int] = mapped_column(
        ForeignKey("groups.group_code", ondelete="CASCADE"), index=True
    )
    class_name: Mapped[str] = mapped_column(String(255))
    class_status: Mapped[bool] = mapped_column(Boolean)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    group: Mapped[Group] = relationship(back_populates="classes")

    pdms: Mapped[list[Pdm]] = relationship(
        back_populates="item_class",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
