"""Entrega de contenido del curador para un `campana_medio`.

`metadatos_escritura` es JSONB porque su estructura varía por tipo de entrega
(p. ej. el editor anti-IA de bloggers guarda métricas de escritura distintas a
las de un reel). `puntuacion_autenticidad` la calcula el editor anti-IA.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from src.models.enums import TipoEntrega, pg_enum


class EntregaContenido(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "entregas_contenido"

    campana_medio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campana_medios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoEntrega] = mapped_column(
        pg_enum(TipoEntrega, "tipo_entrega"), nullable=False
    )
    url_entrega: Mapped[str | None] = mapped_column(String(512), nullable=True)
    contenido_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    puntuacion_autenticidad: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadatos_escritura: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    aprobada_por_artista: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
