"""Sellos discográficos y su relación con artistas.

`sello_artistas` es tabla puente: un artista puede pertenecer a un sello (o a
ninguno) y un sello puede administrar múltiples artistas, con un rol por relación.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import RolSelloArtista, pg_enum


class SelloDiscografico(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sellos_discograficos"

    nombre: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )


class SelloArtista(Base):
    __tablename__ = "sello_artistas"

    sello_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellos_discograficos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    artista_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    rol: Mapped[RolSelloArtista] = mapped_column(
        pg_enum(RolSelloArtista, "rol_sello_artista"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
