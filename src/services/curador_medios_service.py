"""Gestión de medios del curador post-onboarding: stats, CRUD y activación.

Complementa a `curador_medio_service` (alta inicial en onboarding) añadiendo
estadísticas por medio y el toggle activo/inactivo con protección de campañas
activas. La autorización a nivel de recurso (el medio pertenece al curador en
sesión) se valida en cada operación.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.campana_medios import CampanaMedio
from src.models.curador_medios import CuradorMedio
from src.models.dto.curador_medios import (
    MedioConStatsDTO,
    MedioCreateBody,
    MedioStatsDetalleDTO,
    MedioStatsDTO,
    MedioUpdateBody,
    MesStatDTO,
)
from src.models.enums import EstadoCampanaMedio
from src.models.generos import CuradorMedioGenero
from src.services.curador_medio_service import _ensure_generos, _genero_ids
from src.services.exceptions import ConflictError, NotFoundError

# Estados que cuentan como "campaña activa" en el medio (bloquean desactivar).
_ESTADOS_ACTIVOS = (EstadoCampanaMedio.pendiente, EstadoCampanaMedio.aceptada)


async def _stats(session: AsyncSession, medio_id: uuid.UUID) -> MedioStatsDTO:
    row = (
        await session.execute(
            select(
                func.count().label("recibidas"),
                func.count()
                .filter(CampanaMedio.estado == EstadoCampanaMedio.aceptada)
                .label("aceptadas"),
                func.count()
                .filter(CampanaMedio.estado == EstadoCampanaMedio.entregada)
                .label("entregadas"),
            ).where(CampanaMedio.medio_id == medio_id)
        )
    ).one()
    recibidas, aceptadas, entregadas = row.recibidas, row.aceptadas, row.entregadas
    tasa = round((aceptadas + entregadas) / recibidas, 2) if recibidas else 0.0
    return MedioStatsDTO(
        recibidas=recibidas,
        aceptadas=aceptadas,
        entregadas=entregadas,
        tasa_aceptacion=tasa,
    )


async def _get_propio(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> CuradorMedio:
    """Carga un medio del curador (activo o inactivo). → 404 si no es suyo."""
    medio = await session.get(CuradorMedio, medio_id)
    if medio is None or medio.curador_id != curador_id:
        raise NotFoundError("Medio no encontrado")
    return medio


async def _to_dto(
    session: AsyncSession, medio: CuradorMedio
) -> MedioConStatsDTO:
    return MedioConStatsDTO(
        id=str(medio.id),
        nombre=medio.nombre,
        tipo=medio.tipo.value,
        url=medio.url,
        descripcion=medio.descripcion,
        audiencia_estimada=medio.audiencia_estimada,
        activo=medio.activo,
        genero_ids=await _genero_ids(session, medio.id),
        stats=await _stats(session, medio.id),
    )


async def list_con_stats(
    session: AsyncSession, curador_id: uuid.UUID
) -> list[MedioConStatsDTO]:
    medios = (
        await session.scalars(
            select(CuradorMedio)
            .where(CuradorMedio.curador_id == curador_id)
            .order_by(CuradorMedio.created_at)
        )
    ).all()
    return [await _to_dto(session, m) for m in medios]


async def crear(
    session: AsyncSession, curador_id: uuid.UUID, body: MedioCreateBody
) -> MedioConStatsDTO:
    await _ensure_generos(session, body.generos_especializados)
    medio = CuradorMedio(
        curador_id=curador_id,
        nombre=body.nombre,
        tipo=body.tipo,
        url=body.url,
        descripcion=body.descripcion,
        audiencia_estimada=body.audiencia_estimada,
    )
    session.add(medio)
    await session.flush()
    session.add_all(
        [
            CuradorMedioGenero(medio_id=medio.id, genero_id=gid)
            for gid in dict.fromkeys(body.generos_especializados)
        ]
    )
    await session.commit()
    return await _to_dto(session, medio)


async def editar(
    session: AsyncSession,
    medio_id: uuid.UUID,
    curador_id: uuid.UUID,
    body: MedioUpdateBody,
) -> MedioConStatsDTO:
    medio = await _get_propio(session, medio_id, curador_id)

    if body.nombre is not None:
        medio.nombre = body.nombre
    if body.url is not None:
        medio.url = body.url or None
    if body.descripcion is not None:
        medio.descripcion = body.descripcion or None
    if body.audiencia_estimada is not None:
        medio.audiencia_estimada = body.audiencia_estimada

    if body.generos_especializados is not None:
        await _ensure_generos(session, body.generos_especializados)
        await session.execute(
            CuradorMedioGenero.__table__.delete().where(
                CuradorMedioGenero.medio_id == medio_id
            )
        )
        session.add_all(
            [
                CuradorMedioGenero(medio_id=medio_id, genero_id=gid)
                for gid in dict.fromkeys(body.generos_especializados)
            ]
        )

    await session.commit()
    return await _to_dto(session, medio)


async def toggle_activo(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> MedioConStatsDTO:
    medio = await _get_propio(session, medio_id, curador_id)

    if medio.activo:
        # Desactivar: bloquear si hay campañas activas en el medio.
        activas = await session.scalar(
            select(func.count())
            .select_from(CampanaMedio)
            .where(
                CampanaMedio.medio_id == medio_id,
                CampanaMedio.estado.in_(_ESTADOS_ACTIVOS),
            )
        )
        if activas:
            raise ConflictError("Tienes campañas activas en este medio")

    medio.activo = not medio.activo
    await session.commit()
    return await _to_dto(session, medio)


async def stats_detalladas(
    session: AsyncSession, medio_id: uuid.UUID, curador_id: uuid.UUID
) -> MedioStatsDetalleDTO:
    await _get_propio(session, medio_id, curador_id)
    base = await _stats(session, medio_id)

    mes_col = func.to_char(
        func.date_trunc("month", CampanaMedio.created_at), "YYYY-MM"
    )
    filas = (
        await session.execute(
            select(mes_col.label("mes"), func.count().label("n"))
            .where(
                CampanaMedio.medio_id == medio_id,
                CampanaMedio.created_at >= text("now() - interval '6 months'"),
            )
            .group_by(mes_col)
            .order_by(mes_col)
        )
    ).all()

    return MedioStatsDetalleDTO(
        recibidas=base.recibidas,
        aceptadas=base.aceptadas,
        entregadas=base.entregadas,
        tasa_aceptacion=base.tasa_aceptacion,
        por_mes=[MesStatDTO(mes=mes, recibidas=n) for mes, n in filas],
    )
