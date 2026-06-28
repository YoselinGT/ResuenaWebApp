"""Servicio de catálogos: géneros, idiomas, regiones y tipos de medio.

Solo lectura. Los catálogos son seed inmutable (Fase 02); no hay commits aquí.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.catalogos import Idioma, Region
from src.models.enums import TipoMedio
from src.models.generos import GeneroMusical


async def get_generos(session: AsyncSession) -> list[GeneroMusical]:
    stmt = (
        select(GeneroMusical)
        .where(GeneroMusical.activo.is_(True))
        .order_by(GeneroMusical.nombre)
    )
    return list((await session.scalars(stmt)).all())


async def get_idiomas(session: AsyncSession) -> list[Idioma]:
    return list((await session.scalars(select(Idioma).order_by(Idioma.nombre))).all())


async def get_regiones(session: AsyncSession) -> list[Region]:
    return list((await session.scalars(select(Region).order_by(Region.nombre))).all())


def get_tipos_curador_medio() -> list[str]:
    """Valores válidos del ENUM `curador_medios.tipo`."""
    return [t.value for t in TipoMedio]
