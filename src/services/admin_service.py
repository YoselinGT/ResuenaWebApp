"""Servicio del panel de administración: solicitudes de curador y usuarios."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.roles import PERFIL_ADMIN
from src.models.dto.admin import (
    PaginatedSolicitudesDTO,
    PaginatedUsuariosDTO,
    RedDTO,
    SolicitudDetalleDTO,
    SolicitudItemDTO,
    UsuarioAdminDTO,
    UsuarioAdminUpdate,
)
from src.models.enums import EstadoSolicitudCurador, TipoUsuario
from src.models.solicitudes_curador import SolicitudCurador
from src.models.usuario_redes import UsuarioRed
from src.models.usuarios import Usuario
from src.services import bitacora_service, email_service
from src.services.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from src.utils.sanitize import clean_text


def _item(sol: SolicitudCurador, usuario: Usuario) -> SolicitudItemDTO:
    return SolicitudItemDTO(
        id=str(sol.id),
        usuario_id=str(sol.usuario_id),
        nombre_completo=usuario.nombre_completo,
        correo=usuario.correo,
        estado=sol.estado.value,
        tipo_profesional=sol.tipo_profesional,
        url_portfolio=sol.url_portfolio,
        notas_revision=sol.notas_revision,
        revisor_id=str(sol.revisor_id) if sol.revisor_id else None,
        created_at=sol.created_at,
    )


async def list_solicitudes(
    session: AsyncSession,
    *,
    estado: EstadoSolicitudCurador | None = None,
    tipo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedSolicitudesDTO:
    """Lista paginada de solicitudes de curador con filtros (más recientes primero)."""
    filtros = []
    if estado is not None:
        filtros.append(SolicitudCurador.estado == estado)
    if tipo:
        filtros.append(SolicitudCurador.tipo_profesional == tipo)
    if desde is not None:
        filtros.append(SolicitudCurador.created_at >= desde)
    if hasta is not None:
        # `hasta` inclusivo: hasta el final de ese día.
        filtros.append(SolicitudCurador.created_at < hasta + timedelta(days=1))

    total = await session.scalar(
        select(func.count()).select_from(SolicitudCurador).where(*filtros)
    )

    rows = (
        await session.execute(
            select(SolicitudCurador, Usuario)
            .join(Usuario, Usuario.id == SolicitudCurador.usuario_id)
            .where(*filtros)
            .order_by(SolicitudCurador.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    return PaginatedSolicitudesDTO(
        items=[_item(sol, usuario) for sol, usuario in rows],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


async def get_solicitud(
    session: AsyncSession, solicitud_id: uuid.UUID
) -> SolicitudDetalleDTO:
    """Detalle de una solicitud con las redes sociales del curador. → 404."""
    sol = await session.get(SolicitudCurador, solicitud_id)
    if sol is None:
        raise NotFoundError("Solicitud no encontrada")
    usuario = await session.get(Usuario, sol.usuario_id)

    redes = (
        await session.scalars(
            select(UsuarioRed).where(UsuarioRed.usuario_id == sol.usuario_id)
        )
    ).all()

    base = _item(sol, usuario)
    return SolicitudDetalleDTO(
        **base.model_dump(),
        redes=[RedDTO(tipo=r.tipo.value, url=r.url) for r in redes],
    )


async def aprobar_solicitud(
    session: AsyncSession, admin_id: uuid.UUID, solicitud_id: uuid.UUID
) -> SolicitudDetalleDTO:
    """Aprueba una solicitud de curador. → 404 si no existe; 409 si ya aprobada."""
    sol = await session.get(SolicitudCurador, solicitud_id)
    if sol is None:
        raise NotFoundError("Solicitud no encontrada")
    if sol.estado == EstadoSolicitudCurador.aprobada:
        raise ConflictError("La solicitud ya está aprobada")

    sol.estado = EstadoSolicitudCurador.aprobada
    sol.revisor_id = admin_id
    usuario = await session.get(Usuario, sol.usuario_id)

    await email_service.send_aprobacion(usuario.correo, usuario.nombre_completo)
    await bitacora_service.registrar(
        session,
        accion="aprobacion_curador",
        entidad="solicitud_curador",
        entidad_id=str(solicitud_id),
        autor_id=admin_id,
        detalle={"usuario_id": str(sol.usuario_id), "correo": usuario.correo},
    )
    await session.commit()
    return await get_solicitud(session, solicitud_id)


def _usuario_dto(u: Usuario) -> UsuarioAdminDTO:
    return UsuarioAdminDTO(
        id=str(u.id),
        nombre_completo=u.nombre_completo,
        correo=u.correo,
        tipo=u.tipo.value,
        perfil_id=u.perfil_id,
        activo=u.activo,
        created_at=u.created_at,
    )


async def _get_usuario_editable(
    session: AsyncSession, usuario_id: uuid.UUID
) -> Usuario:
    """Carga un usuario editable por admin. → 404 si no existe; 403 si es admin."""
    usuario = await session.get(Usuario, usuario_id)
    if usuario is None:
        raise NotFoundError("Usuario no encontrado")
    if usuario.perfil_id == PERFIL_ADMIN:
        raise ForbiddenError("No se puede modificar a un administrador")
    return usuario


async def update_usuario(
    session: AsyncSession,
    admin_id: uuid.UUID,
    usuario_id: uuid.UUID,
    dto: UsuarioAdminUpdate,
) -> UsuarioAdminDTO:
    """Edita nombre y/o estado activo. Ignora correo/contraseña/tipo. Protege admins."""
    usuario = await _get_usuario_editable(session, usuario_id)
    cambios: dict[str, object] = {}

    if dto.nombre_completo is not None:
        nuevo = clean_text(dto.nombre_completo)
        if not nuevo or len(nuevo) < 2:
            raise ValidationError("El nombre no es válido")
        if nuevo != usuario.nombre_completo:
            cambios["nombre_completo"] = {"antes": usuario.nombre_completo, "despues": nuevo}
            usuario.nombre_completo = nuevo

    if dto.activo is not None and dto.activo != usuario.activo:
        cambios["activo"] = {"antes": usuario.activo, "despues": dto.activo}
        usuario.activo = dto.activo

    if cambios:
        await bitacora_service.registrar(
            session,
            accion="edicion_usuario_admin",
            entidad="usuario",
            entidad_id=str(usuario_id),
            autor_id=admin_id,
            detalle={"cambios": cambios},
        )
        await session.commit()

    return _usuario_dto(usuario)


async def toggle_status_usuario(
    session: AsyncSession, admin_id: uuid.UUID, usuario_id: uuid.UUID
) -> UsuarioAdminDTO:
    """Activa/desactiva un usuario. Protege admins (→403) y → 404 si no existe."""
    usuario = await _get_usuario_editable(session, usuario_id)
    usuario.activo = not usuario.activo
    await bitacora_service.registrar(
        session,
        accion="toggle_status_usuario",
        entidad="usuario",
        entidad_id=str(usuario_id),
        autor_id=admin_id,
        detalle={"activo": usuario.activo},
    )
    await session.commit()
    return _usuario_dto(usuario)


async def list_usuarios(
    session: AsyncSession,
    *,
    tipo: TipoUsuario | None = None,
    activo: bool | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedUsuariosDTO:
    """Lista paginada de usuarios con filtros (más recientes primero)."""
    filtros = []
    if tipo is not None:
        filtros.append(Usuario.tipo == tipo)
    if activo is not None:
        filtros.append(Usuario.activo == activo)
    if desde is not None:
        filtros.append(Usuario.created_at >= desde)
    if hasta is not None:
        filtros.append(Usuario.created_at < hasta + timedelta(days=1))

    total = await session.scalar(
        select(func.count()).select_from(Usuario).where(*filtros)
    )
    usuarios = (
        await session.scalars(
            select(Usuario)
            .where(*filtros)
            .order_by(Usuario.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    return PaginatedUsuariosDTO(
        items=[_usuario_dto(u) for u in usuarios],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


async def rechazar_solicitud(
    session: AsyncSession,
    admin_id: uuid.UUID,
    solicitud_id: uuid.UUID,
    motivo: str,
) -> SolicitudDetalleDTO:
    """Rechaza una solicitud con motivo. → 404 si no existe; 409 si ya rechazada."""
    sol = await session.get(SolicitudCurador, solicitud_id)
    if sol is None:
        raise NotFoundError("Solicitud no encontrada")
    if sol.estado == EstadoSolicitudCurador.rechazada:
        raise ConflictError("La solicitud ya está rechazada")

    motivo_limpio = clean_text(motivo) or motivo.strip()
    sol.estado = EstadoSolicitudCurador.rechazada
    sol.revisor_id = admin_id
    sol.notas_revision = motivo_limpio
    usuario = await session.get(Usuario, sol.usuario_id)

    await email_service.send_rechazo(
        usuario.correo, usuario.nombre_completo, motivo_limpio
    )
    await bitacora_service.registrar(
        session,
        accion="rechazo_curador",
        entidad="solicitud_curador",
        entidad_id=str(solicitud_id),
        autor_id=admin_id,
        detalle={"usuario_id": str(sol.usuario_id), "motivo": motivo_limpio},
    )
    await session.commit()
    return await get_solicitud(session, solicitud_id)
