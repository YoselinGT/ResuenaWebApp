"""Bitácora de eventos — auditoría de acciones críticas.

`detalle` es JSONB de estructura libre por tipo de evento. `entidad_id` se
guarda como texto para poder referenciar entidades con PK UUID o entera.
Nunca registrar passwords, tokens ni datos bancarios aquí.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class BitacoraEvento(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "bitacora_eventos"

    autor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad: Mapped[str] = mapped_column(String(100), nullable=False)
    entidad_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_bitacora_autor", "autor_id", text("created_at DESC")),
        Index(
            "idx_bitacora_entidad",
            "entidad",
            "entidad_id",
            text("created_at DESC"),
        ),
    )
