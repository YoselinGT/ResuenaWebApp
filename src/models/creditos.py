"""Wallet y transacciones de créditos.

`wallets` lleva el saldo con CHECK >= 0. Toda mutación de saldo en la capa de
servicio debe usar `SELECT FOR UPDATE` (regla no negociable). `creditos_transacciones`
es append-only (libro mayor); por eso usa solo `created_at`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from src.models.enums import TipoTransaccionCredito, pg_enum


class CreditoTransaccion(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "creditos_transacciones"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tipo: Mapped[TipoTransaccionCredito] = mapped_column(
        pg_enum(TipoTransaccionCredito, "tipo_transaccion_credito"), nullable=False
    )
    monto: Mapped[int] = mapped_column(Integer, nullable=False)
    referencia_stripe: Mapped[str | None] = mapped_column(String(255), nullable=True)
    campana_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campanas.id", ondelete="SET NULL"),
        nullable=True,
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    monto_usd: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )

    __table_args__ = (
        Index("idx_creditos_usuario", "usuario_id", text("created_at DESC")),
    )


class Wallet(Base):
    __tablename__ = "wallets"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    saldo_creditos: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    saldo_pendiente_retiro: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("saldo_creditos >= 0", name="saldo_creditos_no_negativo"),
        CheckConstraint(
            "saldo_pendiente_retiro >= 0", name="saldo_pendiente_no_negativo"
        ),
    )
