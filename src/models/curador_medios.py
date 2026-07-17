"""Curador-medio — cada canal/medio independiente de un curador.

Un curador (usuario) tiene N medios (una playlist de Spotify, una página de
Facebook de cumbia, un perfil de TikTok de reggaeton…). Las campañas se envían
al medio específico, no al curador en abstracto. Los géneros del medio se
gestionan vía `curador_medio_generos` (ver generos.py).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import TipoMedio, pg_enum


class CuradorMedio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "curador_medios"

    curador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoMedio] = mapped_column(
        pg_enum(TipoMedio, "tipo_medio"), nullable=False
    )
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    audiencia_estimada: Mapped[int | None] = mapped_column(Integer, nullable=True)
    precio_creditos: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )
    descripcion_precio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
