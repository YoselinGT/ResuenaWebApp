"""Redes sociales asociadas al perfil de un usuario."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from src.models.enums import TipoRedSocial, pg_enum


class UsuarioRed(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "usuario_redes"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoRedSocial] = mapped_column(
        pg_enum(TipoRedSocial, "tipo_red_social"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
