"""Parámetros de configuración del sistema (clave/valor).

Valores potencialmente sensibles se guardan cifrados en `valor_cifrado`. El
flag `es_secreto` indica si el valor debe ocultarse en la UI/logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class ParametroConfig(Base):
    __tablename__ = "parametros_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clave: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    valor_cifrado: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_secreto: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
