from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catmat.core.base import Base

if TYPE_CHECKING:
    from catmat.api.models.classes import Class


class Group(Base):
    """ 
        Grupos são responsável por organizar as classes de materiais.
    """
    __tablename__ = "groups"

    group_code: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    group_name: Mapped[str] = mapped_column(String(255))
    group_status: Mapped[bool] = mapped_column(Boolean)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    classes: Mapped[list[Class]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
