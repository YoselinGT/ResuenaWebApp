"""Invitaciones a sellos discográficos.

Un owner/manager invita a un artista (por correo) a unirse al sello con un rol.
El token es de un solo uso; al aceptar se crea la fila en `sello_artistas`. El
índice `idx_invitaciones_sello_correo` acelera la búsqueda de invitaciones por
correo y estado.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from src.models.enums import EstadoInvitacionSello, RolSelloArtista, pg_enum


class InvitacionSello(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "invitaciones_sello"

    sello_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellos_discograficos.id", ondelete="CASCADE"),
        nullable=False,
    )
    correo: Mapped[str] = mapped_column(String(255), nullable=False)
    invitado_artista_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    rol: Mapped[RolSelloArtista] = mapped_column(
        pg_enum(RolSelloArtista, "rol_sello_artista"), nullable=False
    )
    invitado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    estado: Mapped[EstadoInvitacionSello] = mapped_column(
        pg_enum(EstadoInvitacionSello, "estado_invitacion_sello"),
        nullable=False,
        server_default=EstadoInvitacionSello.pendiente.value,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_invitaciones_sello_correo", "correo", "estado"),
    )
