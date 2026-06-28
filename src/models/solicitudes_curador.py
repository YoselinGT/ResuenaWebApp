"""Solicitud de curador — flujo de aprobación admin.

Un usuario que quiere ser curador envía una solicitud; un admin (revisor) la
aprueba o rechaza. El índice `idx_sol_curador_usuario` acelera el panel admin.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import EstadoSolicitudCurador, pg_enum


class SolicitudCurador(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "solicitudes_curador"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    estado: Mapped[EstadoSolicitudCurador] = mapped_column(
        pg_enum(EstadoSolicitudCurador, "estado_solicitud_curador"),
        nullable=False,
        server_default=EstadoSolicitudCurador.pendiente.value,
    )
    notas_revision: Mapped[str | None] = mapped_column(Text, nullable=True)
    revisor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_sol_curador_usuario", "usuario_id", "estado"),
    )
