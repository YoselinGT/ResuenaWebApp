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
    CanalAdminDTO,
    PaginatedCanalesDTO,
    PaginatedSolicitudesDTO,
    RechazarBody,
    RechazarCanalBody,
    SolicitudDetalleDTO,
)
from src.models.enums import EstadoSolicitudCurador
from src.services import admin_service

router = APIRouter(prefix="/admin/solicitudes", tags=["admin"])


@router.get("/canales", response_model=PaginatedCanalesDTO)
async def list_canales(
    estado_revision: str | None = None,
    tipo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> PaginatedCanalesDTO:
    """Lista paginada de canales con info del curador."""
    return await admin_service.list_canales_admin(
        session,
        estado_revision=estado_revision,
        tipo=tipo,
        desde=desde,
        hasta=hasta,
        page=page,
        page_size=page_size,
    )


@router.get("/canales/{canal_id}", response_model=CanalAdminDTO)
async def get_canal(
    canal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> CanalAdminDTO:
    """Detalle de un canal con info del curador."""
    return await admin_service.get_canal_admin(session, canal_id)


@router.post("/canales/{canal_id}/aprobar", response_model=CanalAdminDTO)
async def aprobar_canal_por_id(
    canal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> CanalAdminDTO:
    """Aprueba un canal directamente por su ID."""
    return await admin_service.aprobar_canal_directo(
        session, uuid.UUID(admin.id), canal_id
    )


@router.post("/canales/{canal_id}/rechazar", response_model=CanalAdminDTO)
async def rechazar_canal_por_id(
    canal_id: uuid.UUID,
    body: RechazarCanalBody,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> CanalAdminDTO:
    """Rechaza un canal directamente por su ID."""
    return await admin_service.rechazar_canal_directo(
        session, uuid.UUID(admin.id), canal_id, body.motivo
    )


@router.post("/canales/{canal_id}/pendiente", response_model=CanalAdminDTO)
async def revertir_canal_por_id(
    canal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> CanalAdminDTO:
    """Revierte un canal a pendiente directamente por su ID."""
    return await admin_service.revertir_canal_directo(
        session, uuid.UUID(admin.id), canal_id
    )


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


@router.post(
    "/{solicitud_id}/canales/{medio_id}/aprobar",
    response_model=SolicitudDetalleDTO,
)
async def aprobar_canal(
    solicitud_id: uuid.UUID,
    medio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> SolicitudDetalleDTO:
    return await admin_service.aprobar_canal(
        session, uuid.UUID(admin.id), solicitud_id, medio_id
    )


@router.post(
    "/{solicitud_id}/canales/{medio_id}/rechazar",
    response_model=SolicitudDetalleDTO,
)
async def rechazar_canal(
    solicitud_id: uuid.UUID,
    medio_id: uuid.UUID,
    body: RechazarCanalBody,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> SolicitudDetalleDTO:
    return await admin_service.rechazar_canal(
        session, uuid.UUID(admin.id), solicitud_id, medio_id, body.motivo
    )


@router.post(
    "/{solicitud_id}/canales/{medio_id}/pendiente",
    response_model=SolicitudDetalleDTO,
)
async def revertir_canal(
    solicitud_id: uuid.UUID,
    medio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> SolicitudDetalleDTO:
    return await admin_service.revertir_canal(
        session, uuid.UUID(admin.id), solicitud_id, medio_id
    )
