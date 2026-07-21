"""Servicio del panel de administración: solicitudes de curador y usuarios."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.roles import PERFIL_ADMIN
from src.models.curador_medio_redes import CuradorMedioRed
from src.models.curador_medios import CuradorMedio
from src.models.dto.admin import (
    CanalAdminDTO,
    CanalRedDTO,
    CanalRevisionDTO,
    PaginatedCanalesDTO,
    PaginatedSolicitudesDTO,
    PaginatedUsuariosDTO,
    RedDTO,
    SolicitudDetalleDTO,
    SolicitudItemDTO,
    UsuarioAdminDTO,
    UsuarioAdminUpdate,
)
from src.models.enums import EstadoSolicitudCurador, TipoUsuario
from src.models.generos import CategoriaProfesional, CuradorMedioCategoria, CuradorMedioGenero, GeneroMusical
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


# ── Listado de canales (nuevo flujo centrado en canales) ────────


async def list_canales_admin(
    session: AsyncSession,
    *,
    estado_revision: str | None = None,
    tipo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedCanalesDTO:
    """Lista paginada de canales con info del curador (más recientes primero)."""
    filtros = [CuradorMedio.activo.is_(True)]
    if estado_revision:
        filtros.append(CuradorMedio.estado_revision == estado_revision)
    if tipo:
        filtros.append(CuradorMedio.tipo == tipo)
    if desde is not None:
        filtros.append(CuradorMedio.created_at >= desde)
    if hasta is not None:
        filtros.append(CuradorMedio.created_at < hasta + timedelta(days=1))

    total = await session.scalar(
        select(func.count()).select_from(CuradorMedio).where(*filtros)
    )

    rows = (
        await session.execute(
            select(CuradorMedio, Usuario)
            .join(Usuario, Usuario.id == CuradorMedio.curador_id)
            .where(*filtros)
            .order_by(CuradorMedio.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()

    # Batch load géneros
    medio_ids = [m.id for m, _ in rows]
    generos_por_medio: dict[uuid.UUID, list[str]] = {mid: [] for mid in medio_ids}
    if medio_ids:
        gen_rows = (
            await session.execute(
                select(CuradorMedioGenero.medio_id, GeneroMusical.nombre)
                .join(GeneroMusical, GeneroMusical.id == CuradorMedioGenero.genero_id)
                .where(CuradorMedioGenero.medio_id.in_(medio_ids))
            )
        ).all()
        for medio_id, nombre in gen_rows:
            generos_por_medio[medio_id].append(nombre)

    # Batch load redes
    redes_por_medio: dict[uuid.UUID, list[CanalRedDTO]] = {mid: [] for mid in medio_ids}
    if medio_ids:
        redes_rows = (
            await session.scalars(
                select(CuradorMedioRed)
                .where(CuradorMedioRed.medio_id.in_(medio_ids))
                .order_by(CuradorMedioRed.es_principal.desc())
            )
        ).all()
        for r in redes_rows:
            redes_por_medio[r.medio_id].append(
                CanalRedDTO(tipo=r.tipo, url=r.url, es_principal=r.es_principal)
            )

    # Batch load categorías
    categorias_por_medio: dict[uuid.UUID, list[str]] = {mid: [] for mid in medio_ids}
    if medio_ids:
        cat_rows = (
            await session.execute(
                select(CuradorMedioCategoria.medio_id, CategoriaProfesional.nombre)
                .join(CategoriaProfesional, CategoriaProfesional.id == CuradorMedioCategoria.categoria_id)
                .where(CuradorMedioCategoria.medio_id.in_(medio_ids))
            )
        ).all()
        for medio_id, nombre in cat_rows:
            categorias_por_medio[medio_id].append(nombre)

    items = [
        CanalAdminDTO(
            id=str(m.id),
            nombre=m.nombre,
            tipo=m.tipo.value if hasattr(m.tipo, "value") else m.tipo,
            descripcion=m.descripcion,
            audiencia_estimada=m.audiencia_estimada,
            precio_creditos=m.precio_creditos,
            descripcion_precio=m.descripcion_precio,
            estado_revision=m.estado_revision,
            motivo_rechazo=m.motivo_rechazo,
            revisado_at=m.revisado_at,
            curador_id=str(u.id),
            curador_nombre=u.nombre_completo,
            curador_correo=u.correo,
            generos=generos_por_medio.get(m.id, []),
            categorias=categorias_por_medio.get(m.id, []),
            redes=redes_por_medio.get(m.id, []),
            created_at=m.created_at,
        )
        for m, u in rows
    ]

    return PaginatedCanalesDTO(
        items=items,
        total=total or 0,
        page=page,
        page_size=page_size,
    )


async def get_canal_admin(
    session: AsyncSession, medio_id: uuid.UUID
) -> CanalAdminDTO:
    """Detalle de un canal con info del curador. → 404."""
    medio = await session.get(CuradorMedio, medio_id)
    if medio is None:
        raise NotFoundError("Canal no encontrado")

    usuario = await session.get(Usuario, medio.curador_id)

    # Cargar géneros
    generos_rows = (
        await session.execute(
            select(GeneroMusical.nombre)
            .join(CuradorMedioGenero, CuradorMedioGenero.genero_id == GeneroMusical.id)
            .where(CuradorMedioGenero.medio_id == medio_id)
        )
    ).all()
    generos = [row[0] for row in generos_rows]

    # Cargar redes
    redes_rows = (
        await session.scalars(
            select(CuradorMedioRed)
            .where(CuradorMedioRed.medio_id == medio_id)
            .order_by(CuradorMedioRed.es_principal.desc())
        )
    ).all()
    redes = [
        CanalRedDTO(tipo=r.tipo, url=r.url, es_principal=r.es_principal)
        for r in redes_rows
    ]

    # Cargar categorías
    categorias_rows = (
        await session.execute(
            select(CategoriaProfesional.nombre)
            .join(CuradorMedioCategoria, CuradorMedioCategoria.categoria_id == CategoriaProfesional.id)
            .where(CuradorMedioCategoria.medio_id == medio_id)
        )
    ).all()
    categorias = [row[0] for row in categorias_rows]

    return CanalAdminDTO(
        id=str(medio.id),
        nombre=medio.nombre,
        tipo=medio.tipo.value if hasattr(medio.tipo, "value") else medio.tipo,
        descripcion=medio.descripcion,
        audiencia_estimada=medio.audiencia_estimada,
        precio_creditos=medio.precio_creditos,
        descripcion_precio=medio.descripcion_precio,
        estado_revision=medio.estado_revision,
        motivo_rechazo=medio.motivo_rechazo,
        revisado_at=medio.revisado_at,
        curador_id=str(usuario.id) if usuario else "",
        curador_nombre=usuario.nombre_completo if usuario else "",
        curador_correo=usuario.correo if usuario else "",
        generos=generos,
        categorias=categorias,
        redes=redes,
        created_at=medio.created_at,
    )


async def get_solicitud(
    session: AsyncSession, solicitud_id: uuid.UUID
) -> SolicitudDetalleDTO:
    """Detalle de una solicitud con los canales del curador. → 404."""
    sol = await session.get(SolicitudCurador, solicitud_id)
    if sol is None:
        raise NotFoundError("Solicitud no encontrada")
    usuario = await session.get(Usuario, sol.usuario_id)

    redes = (
        await session.scalars(
            select(UsuarioRed).where(UsuarioRed.usuario_id == sol.usuario_id)
        )
    ).all()

    # Cargar canales activos del curador con géneros
    medios = (
        await session.scalars(
            select(CuradorMedio)
            .where(
                CuradorMedio.curador_id == sol.usuario_id,
                CuradorMedio.activo.is_(True),
            )
            .order_by(CuradorMedio.created_at)
        )
    ).all()

    # Cargar géneros de todos los canales en batch
    medio_ids = [m.id for m in medios]
    generos_por_medio: dict[uuid.UUID, list[str]] = {mid: [] for mid in medio_ids}
    if medio_ids:
        rows = (
            await session.execute(
                select(CuradorMedioGenero.medio_id, GeneroMusical.nombre)
                .join(GeneroMusical, GeneroMusical.id == CuradorMedioGenero.genero_id)
                .where(CuradorMedioGenero.medio_id.in_(medio_ids))
            )
        ).all()
        for medio_id, nombre in rows:
            generos_por_medio[medio_id].append(nombre)

    # Cargar redes de todos los canales en batch
    redes_por_medio: dict[uuid.UUID, list[CanalRedDTO]] = {mid: [] for mid in medio_ids}
    if medio_ids:
        redes_rows = (
            await session.scalars(
                select(CuradorMedioRed)
                .where(CuradorMedioRed.medio_id.in_(medio_ids))
                .order_by(CuradorMedioRed.es_principal.desc())
            )
        ).all()
        for r in redes_rows:
            redes_por_medio[r.medio_id].append(
                CanalRedDTO(tipo=r.tipo, url=r.url, es_principal=r.es_principal)
            )

    # Cargar categorías de todos los canales en batch
    categorias_por_medio: dict[uuid.UUID, list[str]] = {mid: [] for mid in medio_ids}
    if medio_ids:
        cat_rows = (
            await session.execute(
                select(CuradorMedioCategoria.medio_id, CategoriaProfesional.nombre)
                .join(CategoriaProfesional, CategoriaProfesional.id == CuradorMedioCategoria.categoria_id)
                .where(CuradorMedioCategoria.medio_id.in_(medio_ids))
            )
        ).all()
        for medio_id, nombre in cat_rows:
            categorias_por_medio[medio_id].append(nombre)

    canales = [
        CanalRevisionDTO(
            id=str(m.id),
            nombre=m.nombre,
            tipo=m.tipo.value if hasattr(m.tipo, "value") else m.tipo,
            url=m.url,
            descripcion=m.descripcion,
            audiencia_estimada=m.audiencia_estimada,
            precio_creditos=m.precio_creditos,
            descripcion_precio=m.descripcion_precio,
            generos=generos_por_medio.get(m.id, []),
            categorias=categorias_por_medio.get(m.id, []),
            redes=redes_por_medio.get(m.id, []),
            estado_revision=m.estado_revision,
            motivo_rechazo=m.motivo_rechazo,
            revisado_at=m.revisado_at,
        )
        for m in medios
    ]

    base = _item(sol, usuario)
    return SolicitudDetalleDTO(
        **base.model_dump(),
        redes=[RedDTO(tipo=r.tipo.value, url=r.url) for r in redes],
        canales=canales,
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


# ── Aprobación / rechazo por canal ──────────────────────────────

async def _get_canal_de_solicitud(
    session: AsyncSession,
    solicitud_id: uuid.UUID,
    medio_id: uuid.UUID,
) -> tuple[SolicitudCurador, CuradorMedio]:
    """Carga solicitud + canal validando que el canal pertenezca al curador."""
    sol = await session.get(SolicitudCurador, solicitud_id)
    if sol is None:
        raise NotFoundError("Solicitud no encontrada")
    medio = await session.get(CuradorMedio, medio_id)
    if medio is None or medio.curador_id != sol.usuario_id:
        raise NotFoundError("Canal no encontrado")
    return sol, medio


async def _recalcular_estado_solicitud(
    session: AsyncSession, sol: SolicitudCurador
) -> None:
    """Recalcula el estado global de la solicitud basándose en los canales."""
    medios = (
        await session.scalars(
            select(CuradorMedio).where(
                CuradorMedio.curador_id == sol.usuario_id,
                CuradorMedio.activo.is_(True),
            )
        )
    ).all()
    estados = [m.estado_revision for m in medios]
    if "aprobado" in estados:
        sol.estado = EstadoSolicitudCurador.aprobada
    elif all(e == "rechazado" for e in estados):
        sol.estado = EstadoSolicitudCurador.rechazada
    else:
        sol.estado = EstadoSolicitudCurador.pendiente


async def aprobar_canal(
    session: AsyncSession,
    admin_id: uuid.UUID,
    solicitud_id: uuid.UUID,
    medio_id: uuid.UUID,
) -> SolicitudDetalleDTO:
    """Aprueba un canal individual. → 404 si no existe; 409 si ya aprobado."""
    sol, medio = await _get_canal_de_solicitud(session, solicitud_id, medio_id)
    if medio.estado_revision == "aprobado":
        raise ConflictError("El canal ya está aprobado")

    from datetime import UTC, datetime

    medio.estado_revision = "aprobado"
    medio.revisado_por = admin_id
    medio.revisado_at = datetime.now(UTC)
    medio.motivo_rechazo = None

    await _recalcular_estado_solicitud(session, sol)

    # Siempre enviar email de aprobación por canal al curador
    usuario = await session.get(Usuario, sol.usuario_id)
    if usuario:
        await email_service.send_aprobacion_canal(
            usuario.correo, usuario.nombre_completo, medio.nombre
        )

    await bitacora_service.registrar(
        session,
        accion="canal_aprobado",
        entidad="curador_medios",
        entidad_id=str(medio_id),
        autor_id=admin_id,
        detalle={
            "solicitud_id": str(solicitud_id),
            "curador_id": str(sol.usuario_id),
        },
    )
    await session.commit()
    return await get_solicitud(session, solicitud_id)


async def rechazar_canal(
    session: AsyncSession,
    admin_id: uuid.UUID,
    solicitud_id: uuid.UUID,
    medio_id: uuid.UUID,
    motivo: str,
) -> SolicitudDetalleDTO:
    """Rechaza un canal con motivo. → 404 si no existe; 409 si ya rechazado."""
    sol, medio = await _get_canal_de_solicitud(session, solicitud_id, medio_id)
    if medio.estado_revision == "rechazado":
        raise ConflictError("El canal ya está rechazado")

    from datetime import UTC, datetime

    motivo_limpio = clean_text(motivo) or motivo.strip()
    medio.estado_revision = "rechazado"
    medio.motivo_rechazo = motivo_limpio
    medio.revisado_por = admin_id
    medio.revisado_at = datetime.now(UTC)

    await _recalcular_estado_solicitud(session, sol)

    # Siempre enviar email de rechazo por canal al curador
    usuario = await session.get(Usuario, sol.usuario_id)
    if usuario:
        await email_service.send_rechazo_canal(
            usuario.correo, usuario.nombre_completo, medio.nombre, motivo_limpio
        )

    await bitacora_service.registrar(
        session,
        accion="canal_rechazado",
        entidad="curador_medios",
        entidad_id=str(medio_id),
        autor_id=admin_id,
        detalle={
            "solicitud_id": str(solicitud_id),
            "curador_id": str(sol.usuario_id),
            "motivo": motivo_limpio,
        },
    )
    await session.commit()
    return await get_solicitud(session, solicitud_id)


async def revertir_canal(
    session: AsyncSession,
    admin_id: uuid.UUID,
    solicitud_id: uuid.UUID,
    medio_id: uuid.UUID,
) -> SolicitudDetalleDTO:
    """Revierte un canal a pendiente. → 404 si no existe; 409 si ya pendiente."""
    sol, medio = await _get_canal_de_solicitud(session, solicitud_id, medio_id)
    if medio.estado_revision == "pendiente":
        raise ConflictError("El canal ya está pendiente")

    medio.estado_revision = "pendiente"
    medio.motivo_rechazo = None
    medio.revisado_por = None
    medio.revisado_at = None

    await _recalcular_estado_solicitud(session, sol)

    await bitacora_service.registrar(
        session,
        accion="canal_revertido",
        entidad="curador_medios",
        entidad_id=str(medio_id),
        autor_id=admin_id,
        detalle={
            "solicitud_id": str(solicitud_id),
            "curador_id": str(sol.usuario_id),
        },
    )
    await session.commit()
    return await get_solicitud(session, solicitud_id)


# ── Acciones directas por canal (sin solicitud_id) ─────────────


async def _get_canal_directo(
    session: AsyncSession, medio_id: uuid.UUID
) -> tuple[CuradorMedio, SolicitudCurador | None]:
    """Carga un canal y su solicitud asociada (si existe)."""
    medio = await session.get(CuradorMedio, medio_id)
    if medio is None:
        raise NotFoundError("Canal no encontrado")
    sol = await session.scalar(
        select(SolicitudCurador).where(
            SolicitudCurador.usuario_id == medio.curador_id
        )
    )
    return medio, sol


async def aprobar_canal_directo(
    session: AsyncSession, admin_id: uuid.UUID, medio_id: uuid.UUID
) -> CanalAdminDTO:
    """Aprueba un canal directamente por su ID."""
    medio, sol = await _get_canal_directo(session, medio_id)
    if medio.estado_revision == "aprobado":
        raise ConflictError("El canal ya está aprobado")

    from datetime import UTC, datetime

    medio.estado_revision = "aprobado"
    medio.revisado_por = admin_id
    medio.revisado_at = datetime.now(UTC)
    medio.motivo_rechazo = None

    if sol:
        await _recalcular_estado_solicitud(session, sol)

    usuario = await session.get(Usuario, medio.curador_id)
    if usuario:
        await email_service.send_aprobacion_canal(
            usuario.correo, usuario.nombre_completo, medio.nombre
        )

    await bitacora_service.registrar(
        session,
        accion="canal_aprobado",
        entidad="curador_medios",
        entidad_id=str(medio_id),
        autor_id=admin_id,
        detalle={"curador_id": str(medio.curador_id)},
    )
    await session.commit()
    return await get_canal_admin(session, medio_id)


async def rechazar_canal_directo(
    session: AsyncSession, admin_id: uuid.UUID, medio_id: uuid.UUID, motivo: str
) -> CanalAdminDTO:
    """Rechaza un canal directamente por su ID."""
    medio, sol = await _get_canal_directo(session, medio_id)
    if medio.estado_revision == "rechazado":
        raise ConflictError("El canal ya está rechazado")

    from datetime import UTC, datetime

    motivo_limpio = clean_text(motivo) or motivo.strip()
    medio.estado_revision = "rechazado"
    medio.motivo_rechazo = motivo_limpio
    medio.revisado_por = admin_id
    medio.revisado_at = datetime.now(UTC)

    if sol:
        await _recalcular_estado_solicitud(session, sol)

    usuario = await session.get(Usuario, medio.curador_id)
    if usuario:
        await email_service.send_rechazo_canal(
            usuario.correo, usuario.nombre_completo, medio.nombre, motivo_limpio
        )

    await bitacora_service.registrar(
        session,
        accion="canal_rechazado",
        entidad="curador_medios",
        entidad_id=str(medio_id),
        autor_id=admin_id,
        detalle={"curador_id": str(medio.curador_id), "motivo": motivo_limpio},
    )
    await session.commit()
    return await get_canal_admin(session, medio_id)


async def revertir_canal_directo(
    session: AsyncSession, admin_id: uuid.UUID, medio_id: uuid.UUID
) -> CanalAdminDTO:
    """Revierte un canal a pendiente directamente por su ID."""
    medio, sol = await _get_canal_directo(session, medio_id)
    if medio.estado_revision == "pendiente":
        raise ConflictError("El canal ya está pendiente")

    medio.estado_revision = "pendiente"
    medio.motivo_rechazo = None
    medio.revisado_por = None
    medio.revisado_at = None

    if sol:
        await _recalcular_estado_solicitud(session, sol)

    await bitacora_service.registrar(
        session,
        accion="canal_revertido",
        entidad="curador_medios",
        entidad_id=str(medio_id),
        autor_id=admin_id,
        detalle={"curador_id": str(medio.curador_id)},
    )
    await session.commit()
    return await get_canal_admin(session, medio_id)
