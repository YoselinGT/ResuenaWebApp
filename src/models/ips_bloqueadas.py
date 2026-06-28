"""IPs bloqueadas — defensa contra fuerza bruta a nivel de red."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class IpBloqueada(Base):
    __tablename__ = "ips_bloqueadas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, unique=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_ips_blocked_until", "blocked_until"),)
