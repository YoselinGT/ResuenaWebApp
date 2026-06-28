"""Usuario — actor principal de la plataforma (artista o curador).

Los admins se modelan como usuarios con `perfil_id` = Admin. El bloqueo por
intentos fallidos de login usa `blocked_until` + `intentos_fallidos`.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.models.enums import TipoUsuario, pg_enum


class Usuario(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "usuarios"

    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    correo: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoUsuario] = mapped_column(
        pg_enum(TipoUsuario, "tipo_usuario"), nullable=False
    )
    perfil_id: Mapped[int] = mapped_column(
        ForeignKey("perfiles.id", ondelete="RESTRICT"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    blocked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    intentos_fallidos: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    foto_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
