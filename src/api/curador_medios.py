"""Router de gestión de medios del curador (`/curador/medios`).

Requiere sesión de curador. El alta (`POST`) exige además que la solicitud de
curador esté aprobada. La lógica vive en `curador_medios_service`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser, require_tipo
from src.models.dto.curador_medios import (
    MedioConStatsDTO,
    MedioCreateBody,
    MedioStatsDetalleDTO,
    MedioUpdateBody,
)
from src.models.enums import EstadoSolicitudCurador, TipoUsuario
from src.models.solicitudes_curador import SolicitudCurador
from src.services import curador_medios_service
from src.services.exceptions import ForbiddenError

router = APIRouter(prefix="/curador/medios", tags=["curador-medios"])

_solo_curador = require_tipo(TipoUsuario.curador.value)


async def require_curador_aprobado(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
) -> CurrentUser:
    """Exige curador con solicitud aprobada (→403 si pendiente/rechazada)."""
    estado = await session.scalar(
        select(SolicitudCurador.estado)
        .where(SolicitudCurador.usuario_id == uuid.UUID(user.id))
        .order_by(SolicitudCurador.created_at.desc())
        .limit(1)
    )
    if estado != EstadoSolicitudCurador.aprobada:
        raise ForbiddenError("Tu cuenta de curador aún no está aprobada")
    return user


@router.get("", response_model=list[MedioConStatsDTO])
async def listar_medios(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
) -> list[MedioConStatsDTO]:
    return await curador_medios_service.list_con_stats(session, uuid.UUID(user.id))


@router.post("", response_model=MedioConStatsDTO, status_code=status.HTTP_201_CREATED)
async def crear_medio(
    body: MedioCreateBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(require_curador_aprobado),
) -> MedioConStatsDTO:
    return await curador_medios_service.crear(session, uuid.UUID(user.id), body)


@router.patch("/{medio_id}", response_model=MedioConStatsDTO)
async def editar_medio(
    medio_id: uuid.UUID,
    body: MedioUpdateBody,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
) -> MedioConStatsDTO:
    return await curador_medios_service.editar(
        session, medio_id, uuid.UUID(user.id), body
    )


@router.post("/{medio_id}/toggle-activo", response_model=MedioConStatsDTO)
async def toggle_activo(
    medio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
) -> MedioConStatsDTO:
    return await curador_medios_service.toggle_activo(
        session, medio_id, uuid.UUID(user.id)
    )


@router.get("/{medio_id}/stats", response_model=MedioStatsDetalleDTO)
async def stats_medio(
    medio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(_solo_curador),
) -> MedioStatsDetalleDTO:
    return await curador_medios_service.stats_detalladas(
        session, medio_id, uuid.UUID(user.id)
    )
