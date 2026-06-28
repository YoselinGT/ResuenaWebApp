"""Vínculo campaña ↔ medio específico de un curador.

El artista elige a QUÉ medio del curador llega la campaña (no al curador en
abstracto). Cada fila tiene su propio estado, deadline y crédito retenido, de
modo que un curador con varios medios recibe envíos independientes.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import EstadoCampanaMedio, pg_enum


class CampanaMedio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campana_medios"

    campana_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campanas.id", ondelete="CASCADE"),
        nullable=False,
    )
    medio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curador_medios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    curador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estado: Mapped[EstadoCampanaMedio] = mapped_column(
        pg_enum(EstadoCampanaMedio, "estado_campana_medio"),
        nullable=False,
        server_default=EstadoCampanaMedio.pendiente.value,
    )
    fecha_limite: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    creditos_retenidos: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    __table_args__ = (
        Index("idx_campana_medios_curador", "curador_id", "estado"),
        Index("idx_campana_medios_campana", "campana_id"),
        Index(
            "idx_campana_medios_fecha",
            "fecha_limite",
            postgresql_where=text("estado = 'pendiente'"),
        ),
    )
