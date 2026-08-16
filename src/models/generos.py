"""Géneros musicales (catálogo) y sus tablas puente.

- `generos_musicales`: catálogo con PK entera, seedeado en T6.
- `categorias_profesionales`: sub-categorías de cada género.
- `usuario_generos`: géneros preferidos/excluidos de artistas y curadores.
- `curador_medio_generos`: géneros en los que se especializa cada medio.
- `curador_medio_categorias`: categorías que cubre cada canal.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.enums import TipoPreferenciaGenero, pg_enum


class GeneroMusical(Base):
    __tablename__ = "generos_musicales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    categorias: Mapped[list["CategoriaProfesional"]] = relationship(
        back_populates="genero",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


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


class CategoriaProfesional(Base):
    """Sub-categoría de un género musical (ej. Trap dentro de Urbano)."""

    __tablename__ = "categorias_profesionales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos_musicales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    genero: Mapped["GeneroMusical"] = relationship(back_populates="categorias")


class CuradorMedioCategoria(Base):
    """Categoría que cubre un canal del curador (sub-categoría de género)."""

    __tablename__ = "curador_medio_categorias"

    medio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curador_medios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias_profesionales.id", ondelete="RESTRICT"),
        primary_key=True,
    )
