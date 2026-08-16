"""Router de búsqueda de profesionales (`/curadores/disponibles`).

Endpoints para que artistas busquen curadores disponibles para sus campañas.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infra.db import get_session
from src.middleware.auth import CurrentUser
from src.middleware.roles import require_artista
from src.models.curador_medios import CuradorMedio
from src.models.dto.campanas import CanalInfo, CuradorDisponibleResponse
from src.models.generos import CuradorMedioCategoria, CuradorMedioGenero
from src.models.usuarios import Usuario

router = APIRouter(prefix="/curadores", tags=["curadores"])


@router.get("/disponibles", response_model=list[CuradorDisponibleResponse])
async def list_curadores_disponibles(
    tipo_profesional: str | None = None,
    genero_id: int | None = None,
    categoria_id: int | None = None,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_artista),
) -> list[CuradorDisponibleResponse]:
    """Lista curadores disponibles para campañas.

    Solo retorna curadores con al menos un canal aprobado y activo.
    Permite filtrar por tipo de profesional, género y categoría.
    """
    # Subquery: curadores con al menos un canal aprobado
    curadores_aprobados = (
        select(CuradorMedio.curador_id)
        .where(
            CuradorMedio.estado_revision == "aprobado",
            CuradorMedio.activo.is_(True),
        )
        .distinct()
    )

    # Query base: usuarios curadores activos
    query = (
        select(Usuario)
        .where(
            Usuario.perfil_id == 3,  # Curador
            Usuario.activo.is_(True),
            Usuario.id.in_(curadores_aprobados),
        )
        .order_by(Usuario.nombre_completo)
    )

    # Filtrar por tipo de profesional (si se especifica)
    if tipo_profesional:
        # TODO: Agregar campo tipo_profesional a usuarios o curador_medios
        pass

    result = await session.execute(query)
    curadores = list(result.scalars().all())

    # Para cada curador, obtener sus canales aprobados
    response = []
    for curador in curadores:
        canales_query = (
            select(CuradorMedio)
            .where(
                CuradorMedio.curador_id == curador.id,
                CuradorMedio.estado_revision == "aprobado",
                CuradorMedio.activo.is_(True),
            )
            .order_by(CuradorMedio.nombre)
        )

        # Filtrar por género si se especifica
        if genero_id:
            canales_query = canales_query.join(
                CuradorMedioGenero,
                CuradorMedioGenero.medio_id == CuradorMedio.id,
            ).where(CuradorMedioGenero.genero_id == genero_id)

        canales_result = await session.execute(canales_query)
        canales = list(canales_result.scalars().all())

        # Filtrar por categoría si se especifica (búsqueda directa por canal)
        if categoria_id:
            canales_con_categoria = await session.scalars(
                select(CuradorMedio)
                .join(
                    CuradorMedioCategoria,
                    CuradorMedioCategoria.medio_id == CuradorMedio.id,
                )
                .where(
                    CuradorMedio.curador_id == curador.id,
                    CuradorMedio.estado_revision == "aprobado",
                    CuradorMedio.activo.is_(True),
                    CuradorMedioCategoria.categoria_id == categoria_id,
                )
            )
            canales = list(canales_con_categoria.all())

        if not canales:
            continue

        # Obtener géneros de cada canal
        canales_info = []
        for canal in canales:
            generos_result = await session.execute(
                select(CuradorMedioGenero.genero_id).where(
                    CuradorMedioGenero.medio_id == canal.id
                )
            )
            genero_ids = list(generos_result.scalars().all())

            canales_info.append(
                CanalInfo(
                    id=str(canal.id),
                    nombre=canal.nombre,
                    tipo=canal.tipo.value,
                    audiencia_estimada=canal.audiencia_estimada,
                    precio_creditos=canal.precio_creditos,
                    descripcion_precio=canal.descripcion_precio,
                    generos=genero_ids,
                )
            )

        response.append(
            CuradorDisponibleResponse(
                id=str(curador.id),
                nombre_completo=curador.nombre_completo,
                canales=canales_info,
            )
        )

    return response
