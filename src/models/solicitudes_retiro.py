"""Solicitud de retiro de saldo de un curador.

`metodo_pago` es JSONB porque su estructura varía por proveedor (CLABE, PayPal,
Wise). No loguear su contenido (datos bancarios — regla de seguridad).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import EstadoSolicitudRetiro, pg_enum


class SolicitudRetiro(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "solicitudes_retiro"

    curador_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    monto: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[EstadoSolicitudRetiro] = mapped_column(
        pg_enum(EstadoSolicitudRetiro, "estado_solicitud_retiro"),
        nullable=False,
        server_default=EstadoSolicitudRetiro.pendiente.value,
    )
    metodo_pago: Mapped[dict] = mapped_column(JSONB, nullable=False)
    notas_admin: Mapped[str | None] = mapped_column(Text, nullable=True)
