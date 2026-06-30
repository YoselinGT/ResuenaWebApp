"""Router admin de usuarios (`/admin/usuarios`). Solo Admin."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser
from src.middleware.roles import require_admin
from src.models.dto.admin import (
    PaginatedUsuariosDTO,
    UsuarioAdminDTO,
    UsuarioAdminUpdate,
)
from src.models.enums import TipoUsuario
from src.services import admin_service

router = APIRouter(prefix="/admin/usuarios", tags=["admin"])


@router.get("", response_model=PaginatedUsuariosDTO)
async def list_usuarios(
    tipo: TipoUsuario | None = None,
    activo: bool | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> PaginatedUsuariosDTO:
    return await admin_service.list_usuarios(
        session,
        tipo=tipo,
        activo=activo,
        desde=desde,
        hasta=hasta,
        page=page,
        page_size=page_size,
    )


@router.patch("/{usuario_id}", response_model=UsuarioAdminDTO)
async def update_usuario(
    usuario_id: uuid.UUID,
    body: UsuarioAdminUpdate,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> UsuarioAdminDTO:
    return await admin_service.update_usuario(
        session, uuid.UUID(admin.id), usuario_id, body
    )


@router.post("/{usuario_id}/toggle-status", response_model=UsuarioAdminDTO)
async def toggle_status(
    usuario_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    admin: CurrentUser = Depends(require_admin),
) -> UsuarioAdminDTO:
    return await admin_service.toggle_status_usuario(
        session, uuid.UUID(admin.id), usuario_id
    )
