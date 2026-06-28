"""Preferencias de onboarding del usuario (datos progresivos, opcionales).

Separadas de `usuarios` para evitar NULL masivos. Idiomas y regiones se
normalizan en tablas puente (no JSON) para permitir matching indexado.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CHAR,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.enums import TipoLanzamientos, pg_enum


class UsuarioPreferencias(Base):
    __tablename__ = "usuario_preferencias"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    apertura_musical: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="50"
    )
    acepta_todos_idiomas: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    tipo_lanzamientos: Mapped[TipoLanzamientos | None] = mapped_column(
        pg_enum(TipoLanzamientos, "tipo_lanzamientos"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "apertura_musical BETWEEN 0 AND 100",
            name="apertura_musical_rango",
        ),
    )


class UsuarioPreferenciaIdioma(Base):
    __tablename__ = "usuario_preferencias_idiomas"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    idioma_codigo: Mapped[str] = mapped_column(
        CHAR(2),
        ForeignKey("idiomas.codigo", ondelete="RESTRICT"),
        primary_key=True,
    )


class UsuarioPreferenciaRegion(Base):
    __tablename__ = "usuario_preferencias_regiones"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    region_codigo: Mapped[str] = mapped_column(
        CHAR(2),
        ForeignKey("regiones.codigo", ondelete="RESTRICT"),
        primary_key=True,
    )
