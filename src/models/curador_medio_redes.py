"""Redes sociales de un canal del curador.

Cada canal (`curador_medios`) puede tener N redes sociales asociadas
(TikTok, Instagram, YouTube, etc.). La red principal sincroniza su URL
con `curador_medios.url` por compatibilidad.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class CuradorMedioRed(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "curador_medio_redes"

    medio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curador_medios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    es_principal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    medio: Mapped["CuradorMedio"] = relationship(back_populates="redes")
