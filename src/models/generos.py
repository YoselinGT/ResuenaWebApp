"""Géneros musicales (catálogo) y sus tablas puente.

- `generos_musicales`: catálogo con PK entera, seedeado en T6.
- `usuario_generos`: géneros preferidos/excluidos de artistas y curadores.
- `curador_medio_generos`: géneros en los que se especializa cada medio.
  Reemplaza el antiguo `generos_especializados JSON` para mantener integridad
  referencial y permitir filtrar medios por género con JOIN indexado.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.enums import TipoPreferenciaGenero, pg_enum


class GeneroMusical(Base):
    __tablename__ = "generos_musicales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class UsuarioGenero(Base):
    __tablename__ = "usuario_generos"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos_musicales.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    tipo: Mapped[TipoPreferenciaGenero] = mapped_column(
        pg_enum(TipoPreferenciaGenero, "tipo_preferencia_genero"), nullable=False
    )


class CuradorMedioGenero(Base):
    __tablename__ = "curador_medio_generos"

    medio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curador_medios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos_musicales.id", ondelete="RESTRICT"),
        primary_key=True,
    )
