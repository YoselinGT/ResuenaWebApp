"""Guards de rol (RBAC simplificado de Resuena).

Resuena no necesita el RBAC granular del Portal Vendedores: basta con tres
perfiles base (Admin=1, Artista=2, Curador=3, seedeados en la migración 0002).
Estos guards son dependencias FastAPI que se apoyan en `get_current_user`
(JWT de cookie) y, cuando aplica, verifican estado activo y aprobación en BD.

Las excepciones de dominio (`ForbiddenError`) las traduce el handler central a
403; `get_current_user` ya lanza 401 si no hay sesión.
"""

from __future__ import annotations

import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser, get_current_user
from src.models.enums import EstadoSolicitudCurador
from src.models.solicitudes_curador import SolicitudCurador
from src.models.usuarios import Usuario
from src.services.exceptions import ForbiddenError

# Perfiles base (ver seed migración 0002).
PERFIL_ADMIN = 1
PERFIL_ARTISTA = 2
PERFIL_CURADOR = 3


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Exige perfil Admin. → 403 en caso contrario."""
    if user.perfil_id != PERFIL_ADMIN:
        raise ForbiddenError("Requiere permisos de administrador")
    return user


async def _ensure_activo(session: AsyncSession, user: CurrentUser) -> Usuario:
    usuario = await session.get(Usuario, uuid.UUID(user.id))
    if usuario is None or not usuario.activo:
        raise ForbiddenError("Tu cuenta está inactiva")
    return usuario


async def require_artista(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Exige perfil Artista y cuenta activa."""
    if user.perfil_id != PERFIL_ARTISTA:
        raise ForbiddenError("Solo artistas pueden realizar esta acción")
    await _ensure_activo(session, user)
    return user


async def require_curador_aprobado(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Exige perfil Curador, cuenta activa y solicitud aprobada."""
    if user.perfil_id != PERFIL_CURADOR:
        raise ForbiddenError("Solo curadores pueden realizar esta acción")
    await _ensure_activo(session, user)
    estado = await session.scalar(
        select(SolicitudCurador.estado)
        .where(SolicitudCurador.usuario_id == uuid.UUID(user.id))
        .order_by(SolicitudCurador.created_at.desc())
        .limit(1)
    )
    if estado != EstadoSolicitudCurador.aprobada:
        raise ForbiddenError("Tu cuenta de curador aún no está aprobada")
    return user
