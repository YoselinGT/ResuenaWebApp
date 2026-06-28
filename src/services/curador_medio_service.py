"""Servicio CRUD de medios (canales) del curador.

Cada medio tiene géneros especializados en `curador_medio_generos`. El borrado
es lógico (`activo=False`). Toda operación verifica que el medio pertenezca al
curador autenticado (autorización a nivel de recurso).
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dto.onboarding import CuradorMedioDTO, CuradorMedioOutDTO
from src.models.generos import CuradorMedioGenero, GeneroMusical
from src.models.curador_medios import CuradorMedio
from src.services.exceptions import NotFoundError, ValidationError


async def _ensure_generos(session: AsyncSession, genero_ids: list[int]) -> None:
    if not genero_ids:
        return
    encontrados = set(
        (await session.scalars(
            select(GeneroMusical.id).where(GeneroMusical.id.in_(set(genero_ids)))
        )).all()
    )
    faltantes = set(genero_ids) - encontrados
    if faltantes:
        raise ValidationError(f"Géneros inexistentes: {sorted(faltantes)}")


async def _genero_ids(session: AsyncSession, medio_id: uuid.UUID) -> list[int]:
    return list(
        (await session.scalars(
            select(CuradorMedioGenero.genero_id).where(
                CuradorMedioGenero.medio_id == medio_id
            )
        )).all()
    )


def _to_out(medio: CuradorMedio, genero_ids: list[int]) -> CuradorMedioOutDTO:
    return CuradorMedioOutDTO(
        id=str(medio.id),
        nombre=medio.nombre,
        tipo=medio.tipo.value if hasattr(medio.tipo, "value") else medio.tipo,
        url=medio.url,
        descripcion=medio.descripcion,
        audiencia_estimada=medio.audiencia_estimada,
        genero_ids=genero_ids,
    )


async def _get_propio(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> CuradorMedio:
    medio = await session.get(CuradorMedio, medio_id)
    if medio is None or medio.curador_id != curador_id or not medio.activo:
        raise NotFoundError("Medio no encontrado")
    return medio


async def add_medio(
    session: AsyncSession, curador_id: uuid.UUID, dto: CuradorMedioDTO
) -> CuradorMedioOutDTO:
    await _ensure_generos(session, dto.genero_ids)
    medio = CuradorMedio(
        curador_id=curador_id,
        nombre=dto.nombre,
        tipo=dto.tipo,
        url=dto.url,
        descripcion=dto.descripcion,
        audiencia_estimada=dto.audiencia_estimada,
    )
    session.add(medio)
    await session.flush()
    session.add_all(
        [
            CuradorMedioGenero(medio_id=medio.id, genero_id=gid)
            for gid in dict.fromkeys(dto.genero_ids)
        ]
    )
    await session.commit()
    return _to_out(medio, list(dict.fromkeys(dto.genero_ids)))


async def update_medio(
    session: AsyncSession,
    medio_id: uuid.UUID,
    curador_id: uuid.UUID,
    dto: CuradorMedioDTO,
) -> CuradorMedioOutDTO:
    medio = await _get_propio(session, medio_id, curador_id)
    await _ensure_generos(session, dto.genero_ids)
    medio.nombre = dto.nombre
    medio.tipo = dto.tipo
    medio.url = dto.url
    medio.descripcion = dto.descripcion
    medio.audiencia_estimada = dto.audiencia_estimada
    await session.execute(
        delete(CuradorMedioGenero).where(CuradorMedioGenero.medio_id == medio_id)
    )
    session.add_all(
        [
            CuradorMedioGenero(medio_id=medio_id, genero_id=gid)
            for gid in dict.fromkeys(dto.genero_ids)
        ]
    )
    await session.commit()
    return _to_out(medio, list(dict.fromkeys(dto.genero_ids)))


async def delete_medio(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> None:
    medio = await _get_propio(session, medio_id, curador_id)
    medio.activo = False
    await session.commit()


async def list_medios(
    session: AsyncSession, curador_id: uuid.UUID
) -> list[CuradorMedioOutDTO]:
    medios = (
        await session.scalars(
            select(CuradorMedio)
            .where(CuradorMedio.curador_id == curador_id, CuradorMedio.activo.is_(True))
            .order_by(CuradorMedio.created_at)
        )
    ).all()
    return [_to_out(m, await _genero_ids(session, m.id)) for m in medios]
