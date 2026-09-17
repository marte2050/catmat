from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catmat.api.models.base import Base

if TYPE_CHECKING:
    from catmat.api.models.pdm import Pdm


class Item(Base):
    """
    Items representa a tabela de itens do Catmat, que contém informações sobre os produtos ou serviços cadastrados no sistema. 
    Cada item possui um código único, descrição, status, informações sobre sustentabilidade, código e descrição NCM, entre outros atributos. 
    A tabela também mantém um relacionamento com a tabela de PDMs (Plano Descritivo de Materiais).
    """
    __tablename__ = "items"

    item_code: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    pdm_code: Mapped[int] = mapped_column(
        ForeignKey("pdms.pdm_code", ondelete="CASCADE"), index=True
    )
    item_description: Mapped[str] = mapped_column(Text)
    item_status: Mapped[bool] = mapped_column(Boolean)
    is_sustainable: Mapped[bool] = mapped_column(Boolean, default=False)
    ncm_code: Mapped[str | None] = mapped_column(String(20))
    ncm_description: Mapped[str | None] = mapped_column(Text)
    applies_preference_margin: Mapped[bool | None] = mapped_column(Boolean)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    pdm: Mapped[Pdm] = relationship(back_populates="items")

    __table_args__ = (
        Index(
            "ix_items_status_active",
            "item_status",
            postgresql_where=text("item_status"),
        ),
    )
