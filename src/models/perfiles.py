"""Perfil — catálogo de roles base (Admin / Artista / Curador).

PK entera porque es un catálogo con IDs estables seedeados (1=Admin, 2=Artista,
3=Curador). El RBAC fino se construye sobre estos perfiles en fases posteriores.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Perfil(Base):
    __tablename__ = "perfiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
