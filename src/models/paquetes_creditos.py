"""Paquetes de créditos configurables por el admin.

Reemplaza los paquetes hardcodeados de la fase 06. Cada paquete define
`cantidad_creditos` y `precio_total_usd`; los campos derivados (precio_por_credito,
artista_paga_estimado, etc.) se calculan en `paquetes_service` y **nunca** se
almacenan en BD.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, UUIDPrimaryKeyMixin


class PaqueteCredito(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "paquetes_creditos"

    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad_creditos: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_total_usd: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )
    comision_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    destacado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "cantidad_creditos > 0",
            name="ck_paquetes_creditos_cantidad_positiva",
        ),
        CheckConstraint(
            "precio_total_usd > 0",
            name="ck_paquetes_creditos_precio_positivo",
        ),
    )
