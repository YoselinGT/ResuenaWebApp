"""Catálogos de idiomas y regiones para el matching artista↔curador.

PK = código ISO (natural key estable). Tablas normalizadas en vez de JSON para
poder filtrar por idioma/región con índice. Seed en la migración inicial (T4).
"""

from __future__ import annotations

from sqlalchemy import CHAR, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Idioma(Base):
    __tablename__ = "idiomas"

    # ISO 639-1 (ej. 'es', 'en')
    codigo: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)


class Region(Base):
    __tablename__ = "regiones"

    # ISO 3166-1 alpha-2 (ej. 'MX', 'US')
    codigo: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
