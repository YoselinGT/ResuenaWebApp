"""Router admin de solicitudes de curador (`/admin/solicitudes`). Solo Admin."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser
from src.middleware.roles import require_admin
from src.models.dto.admin import (
    PaginatedSolicitudesDTO,
    RechazarBody,
    SolicitudDetalleDTO,
)
from src.models.enums import EstadoSolicitudCurador
from src.services import admin_service

router = APIRouter(prefix="/admin/solicitudes", tags=["admin"])


@router.get("", response_model=PaginatedSolicitudesDTO)
async def list_solicitudes(
    estado: EstadoSolicitudCurador | None = None,
    tipo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> PaginatedSolicitudesDTO:
    return await admin_service.list_solicitudes(
        session,
        estado=estado,
        tipo=tipo,
        desde=desde,
        hasta=hasta,
        page=page,
        page_size=page_size,
    )


@router.get("/{solicitud_id}", response_model=SolicitudDetalleDTO)
async def get_solicitud(
    solicitud_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> SolicitudDetalleDTO:
    return await admin_service.get_solicitud(session, solicitud_id)


@router.post("/{solicitud_id}/aprobar", response_model=SolicitudDetalleDTO)
async def aprobar_solicitud(
    solicitud_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> SolicitudDetalleDTO:
    return await admin_service.aprobar_solicitud(
        session, uuid.UUID(admin.id), solicitud_id
    )


@router.post("/{solicitud_id}/rechazar", response_model=SolicitudDetalleDTO)
async def rechazar_solicitud(
    solicitud_id: uuid.UUID,
    body: RechazarBody,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> SolicitudDetalleDTO:
    return await admin_service.rechazar_solicitud(
        session, uuid.UUID(admin.id), solicitud_id, body.motivo
    )
