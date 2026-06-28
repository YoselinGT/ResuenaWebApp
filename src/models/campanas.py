"""Campaña musical creada por un artista (o por un sello en su nombre).

Nota de almacenamiento: los campos `url_*` guardan **claves S3** (ej.
`campanas-audio/<uuid>/audio.mp3`), no URLs. Las URLs presigned se generan al
servir (regla no negociable de almacenamiento).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import EstadoCampana, pg_enum


class Campana(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campanas"

    artista_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sello_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellos_discograficos.id", ondelete="SET NULL"),
        nullable=True,
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    url_audio: Mapped[str] = mapped_column(String(512), nullable=False)
    url_imagen: Mapped[str | None] = mapped_column(String(512), nullable=True)
    url_material: Mapped[str | None] = mapped_column(String(512), nullable=True)
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos_musicales.id", ondelete="RESTRICT"), nullable=False
    )
    estado: Mapped[EstadoCampana] = mapped_column(
        pg_enum(EstadoCampana, "estado_campana"),
        nullable=False,
        server_default=EstadoCampana.borrador.value,
    )
    creditos_usados: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    __table_args__ = (
        Index("idx_campanas_artista", "artista_id", "estado"),
        Index("idx_campanas_estado", "estado"),
    )
