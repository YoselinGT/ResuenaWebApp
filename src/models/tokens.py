"""Tokens de un solo uso (registro, reset de password, confirmación de email).

Antes de consumir un token, la capa de servicio debe verificarlo con
`SELECT FOR UPDATE` (regla no negociable). `idx_tokens_expires` es parcial:
solo indexa tokens aún no consumidos.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from src.models.enums import TipoToken, pg_enum


class Token(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "tokens"

    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    tipo: Mapped[TipoToken] = mapped_column(
        pg_enum(TipoToken, "tipo_token"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "idx_tokens_expires",
            "expires_at",
            postgresql_where=text("consumed_at IS NULL"),
        ),
    )
