"""Servicio de sellos discográficos.

Un sello agrupa artistas bajo una marca. El creador queda como `owner` en
`sello_artistas`. Invariante: un artista pertenece a un solo sello activo a la
vez (ver docs/fase-04b.md). El logo se guarda como clave S3 vía StorageService.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.infra.storage import StorageService
from src.models.dto.sellos import (
    InvitacionDetalleDTO,
    InvitacionOutDTO,
    MiembroDTO,
    SelloDetalleDTO,
    SelloOutDTO,
)
from src.models.enums import EstadoInvitacionSello, RolSelloArtista, TipoUsuario
from src.models.invitaciones_sello import InvitacionSello
from src.models.sellos import SelloArtista, SelloDiscografico
from src.models.usuarios import Usuario
from src.services import bitacora_service, email_service
from src.services.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    TokenConsumidoError,
    TokenExpiradoError,
    TokenInvalidoError,
    ValidationError,
)
from src.utils.images import JPEG_MIME, process_jpeg_square
from src.utils.sanitize import clean_text

settings = get_settings()

LOGO_SIZE_PX = 256
LOGO_PREFIX = "sellos-logo"
LOGO_URL_TTL_SECONDS = 3600
INVITACION_TTL_DAYS = 7
_TOKEN_BYTES = 32

# Orden de presentación de roles (owner primero).
_ROL_ORDEN = {
    RolSelloArtista.owner.value: 0,
    RolSelloArtista.manager.value: 1,
    RolSelloArtista.artista.value: 2,
}


async def _logo_url(storage: StorageService, sello: SelloDiscografico) -> str | None:
    if not sello.logo_path:
        return None
    return await storage.presigned_url(sello.logo_path, LOGO_URL_TTL_SECONDS)


async def _membership(
    session: AsyncSession, sello_id: uuid.UUID, artista_id: uuid.UUID
) -> SelloArtista | None:
    return await session.scalar(
        select(SelloArtista).where(
            SelloArtista.sello_id == sello_id,
            SelloArtista.artista_id == artista_id,
            SelloArtista.activo.is_(True),
        )
    )


async def _pertenece_a_algun_sello(
    session: AsyncSession, artista_id: uuid.UUID
) -> bool:
    existe = await session.scalar(
        select(SelloArtista.sello_id).where(
            SelloArtista.artista_id == artista_id,
            SelloArtista.activo.is_(True),
        )
    )
    return existe is not None


async def _require_rol(
    session: AsyncSession,
    sello_id: uuid.UUID,
    actor_id: uuid.UUID,
    allowed: set[str],
) -> SelloArtista:
    """Carga la membresía activa del actor en el sello y valida su rol.

    → 403 si no es miembro o su rol no está permitido.
    """
    membresia = await _membership(session, sello_id, actor_id)
    if membresia is None:
        raise ForbiddenError("No perteneces a este sello")
    if membresia.rol.value not in allowed:
        raise ForbiddenError("No tienes permiso para esta acción en el sello")
    return membresia


async def _to_miembro(
    storage: StorageService, u: Usuario, rol: RolSelloArtista, activo: bool
) -> MiembroDTO:
    return MiembroDTO(
        id=str(u.id),
        nombre_completo=u.nombre_completo,
        correo=u.correo,
        rol=rol.value,
        activo=activo,
        foto_url=(
            await storage.presigned_url(u.foto_path, LOGO_URL_TTL_SECONDS)
            if u.foto_path
            else None
        ),
    )


async def _build_detalle(
    session: AsyncSession,
    storage: StorageService,
    sello: SelloDiscografico,
    mi_rol: str,
) -> SelloDetalleDTO:
    rows = (
        await session.execute(
            select(Usuario, SelloArtista.rol, SelloArtista.activo)
            .join(SelloArtista, SelloArtista.artista_id == Usuario.id)
            .where(
                SelloArtista.sello_id == sello.id,
                SelloArtista.activo.is_(True),
            )
        )
    ).all()

    miembros = [await _to_miembro(storage, u, rol, activo) for u, rol, activo in rows]
    miembros.sort(key=lambda m: _ROL_ORDEN.get(m.rol, 99))

    return SelloDetalleDTO(
        id=str(sello.id),
        nombre=sello.nombre,
        descripcion=sello.descripcion,
        website=sello.website,
        logo_url=await _logo_url(storage, sello),
        rol=mi_rol,
        miembros=miembros,
    )


async def create_sello(
    session: AsyncSession,
    storage: StorageService,
    artista_id: uuid.UUID,
    *,
    nombre: str,
    descripcion: str | None = None,
    website: str | None = None,
    logo: bytes | None = None,
) -> SelloOutDTO:
    """Crea un sello y deja al artista como owner.

    → 409 si el artista ya pertenece a un sello activo o el nombre ya existe.
    → 422 si el nombre es inválido.
    """
    nombre_limpio = clean_text(nombre)
    if not nombre_limpio or len(nombre_limpio) < 2:
        raise ValidationError("El nombre del sello no es válido")

    # Invariante: un artista pertenece a un solo sello activo.
    if await _pertenece_a_algun_sello(session, artista_id):
        raise ConflictError("Ya perteneces a un sello activo")

    existe_nombre = await session.scalar(
        select(SelloDiscografico.id).where(
            SelloDiscografico.nombre == nombre_limpio
        )
    )
    if existe_nombre is not None:
        raise ConflictError("Ya existe un sello con ese nombre")

    sello = SelloDiscografico(
        nombre=nombre_limpio,
        descripcion=clean_text(descripcion),
        website=clean_text(website),
        created_by=artista_id,
    )
    session.add(sello)
    await session.flush()  # asigna sello.id

    session.add(
        SelloArtista(
            sello_id=sello.id,
            artista_id=artista_id,
            rol=RolSelloArtista.owner,
            activo=True,
        )
    )

    if logo is not None:
        jpeg = process_jpeg_square(logo, size=LOGO_SIZE_PX)
        key = f"{LOGO_PREFIX}/{sello.id}.jpg"
        await storage.upload(key, jpeg, JPEG_MIME)
        sello.logo_path = key

    await bitacora_service.registrar(
        session,
        accion="Creación de sello",
        entidad="sello",
        entidad_id=str(sello.id),
        autor_id=artista_id,
        detalle={"nombre": nombre_limpio},
    )
    await session.commit()

    return SelloOutDTO(
        id=str(sello.id),
        nombre=sello.nombre,
        descripcion=sello.descripcion,
        website=sello.website,
        logo_url=await _logo_url(storage, sello),
        rol=RolSelloArtista.owner.value,
    )


async def get_mi_sello(
    session: AsyncSession,
    storage: StorageService,
    artista_id: uuid.UUID,
) -> SelloDetalleDTO | None:
    """Devuelve el sello activo del artista (con miembros) o None si no tiene."""
    mi_membresia = await session.scalar(
        select(SelloArtista).where(
            SelloArtista.artista_id == artista_id,
            SelloArtista.activo.is_(True),
        )
    )
    if mi_membresia is None:
        return None

    sello = await session.get(SelloDiscografico, mi_membresia.sello_id)
    if sello is None:
        return None

    return await _build_detalle(session, storage, sello, mi_membresia.rol.value)


_EDITORES = {RolSelloArtista.owner.value, RolSelloArtista.manager.value}
_SOLO_OWNER = {RolSelloArtista.owner.value}


async def update_sello(
    session: AsyncSession,
    storage: StorageService,
    actor_id: uuid.UUID,
    sello_id: uuid.UUID,
    *,
    nombre: str | None = None,
    descripcion: str | None = None,
    website: str | None = None,
    logo: bytes | None = None,
) -> SelloDetalleDTO:
    """Edita un sello. Solo owner o manager. Devuelve el detalle actualizado.

    → 404 si el sello no existe; 403 si el actor no es owner/manager; 409 si el
    nombre nuevo ya existe; 422 si el nombre es inválido.
    """
    sello = await session.get(SelloDiscografico, sello_id)
    if sello is None:
        raise NotFoundError("Sello no encontrado")

    membresia = await _require_rol(session, sello_id, actor_id, _EDITORES)

    cambios: dict[str, str | None] = {}

    if nombre is not None:
        limpio = clean_text(nombre)
        if not limpio or len(limpio) < 2:
            raise ValidationError("El nombre del sello no es válido")
        if limpio != sello.nombre:
            existe = await session.scalar(
                select(SelloDiscografico.id).where(
                    SelloDiscografico.nombre == limpio,
                    SelloDiscografico.id != sello_id,
                )
            )
            if existe is not None:
                raise ConflictError("Ya existe un sello con ese nombre")
            cambios["nombre"] = limpio
            sello.nombre = limpio

    if descripcion is not None:
        nuevo = clean_text(descripcion) or None
        if nuevo != sello.descripcion:
            cambios["descripcion"] = nuevo
            sello.descripcion = nuevo

    if website is not None:
        nuevo = clean_text(website) or None
        if nuevo != sello.website:
            cambios["website"] = nuevo
            sello.website = nuevo

    if logo is not None:
        jpeg = process_jpeg_square(logo, size=LOGO_SIZE_PX)
        key = f"{LOGO_PREFIX}/{sello.id}.jpg"
        await storage.upload(key, jpeg, JPEG_MIME)
        sello.logo_path = key
        cambios["logo"] = "actualizado"

    if cambios:
        await bitacora_service.registrar(
            session,
            accion="Actualización de sello",
            entidad="sello",
            entidad_id=str(sello_id),
            autor_id=actor_id,
            detalle={"cambios": cambios},
        )
        await session.commit()

    return await _build_detalle(session, storage, sello, membresia.rol.value)


async def invitar(
    session: AsyncSession,
    actor_id: uuid.UUID,
    sello_id: uuid.UUID,
    correo: str,
    rol: str,
) -> InvitacionOutDTO:
    """Invita a un artista al sello. Solo owner/manager.

    → 404 si el sello o el artista no existen; 403 si el actor no es owner/
    manager; 422 si el invitado no es artista activo o el rol es inválido;
    409 si ya pertenece a un sello o ya tiene invitación pendiente.
    """
    sello = await session.get(SelloDiscografico, sello_id)
    if sello is None:
        raise NotFoundError("Sello no encontrado")

    await _require_rol(session, sello_id, actor_id, _EDITORES)

    if rol not in {RolSelloArtista.manager.value, RolSelloArtista.artista.value}:
        raise ValidationError("Rol de invitación inválido")

    invitado = await session.scalar(
        select(Usuario).where(Usuario.correo == correo)
    )
    if invitado is None:
        raise NotFoundError("No existe un usuario con ese correo")
    if invitado.tipo != TipoUsuario.artista:
        raise ValidationError("Solo puedes invitar artistas")
    if not invitado.activo:
        raise ValidationError("La cuenta de ese artista no está activa")
    if invitado.id == actor_id:
        raise ValidationError("No puedes invitarte a ti mismo")
    if await _pertenece_a_algun_sello(session, invitado.id):
        raise ConflictError("Ese artista ya pertenece a un sello")

    pendiente = await session.scalar(
        select(InvitacionSello.id).where(
            InvitacionSello.sello_id == sello_id,
            InvitacionSello.invitado_artista_id == invitado.id,
            InvitacionSello.estado == EstadoInvitacionSello.pendiente,
        )
    )
    if pendiente is not None:
        raise ConflictError("Ese artista ya tiene una invitación pendiente")

    token = secrets.token_urlsafe(_TOKEN_BYTES)
    invitacion = InvitacionSello(
        sello_id=sello_id,
        correo=invitado.correo,
        invitado_artista_id=invitado.id,
        rol=RolSelloArtista(rol),
        invitado_por=actor_id,
        token=token,
        estado=EstadoInvitacionSello.pendiente,
        expires_at=datetime.now(UTC) + timedelta(days=INVITACION_TTL_DAYS),
    )
    session.add(invitacion)
    await session.flush()

    actor = await session.get(Usuario, actor_id)
    url = f"{settings.frontend_url}/artista/sello/invitacion/{token}"
    await email_service.send_invitacion_sello(
        invitado.correo,
        sello.nombre,
        actor.nombre_completo if actor else "Un sello",
        rol,
        url,
    )

    await bitacora_service.registrar(
        session,
        accion="Invitación a sello",
        entidad="sello",
        entidad_id=str(sello_id),
        autor_id=actor_id,
        detalle={"invitado": invitado.correo, "rol": rol},
    )
    await session.commit()

    return InvitacionOutDTO(
        id=str(invitacion.id),
        correo=invitacion.correo,
        rol=rol,
        estado=invitacion.estado.value,
        expires_at=invitacion.expires_at,
    )


async def aceptar_invitacion(
    session: AsyncSession,
    storage: StorageService,
    actor_id: uuid.UUID,
    token: str,
) -> SelloDetalleDTO:
    """El artista en sesión acepta una invitación y entra al sello.

    → 400 token inválido/consumido; 410 expirado; 403 si la invitación no es
    para el actor; 409 si el artista ya pertenece a un sello.
    """
    invitacion = (
        await session.execute(
            select(InvitacionSello)
            .where(InvitacionSello.token == token)
            .with_for_update()
        )
    ).scalar_one_or_none()

    if invitacion is None:
        raise TokenInvalidoError("Invitación inválida")
    if (
        invitacion.estado != EstadoInvitacionSello.pendiente
        or invitacion.consumed_at is not None
    ):
        raise TokenConsumidoError("La invitación ya fue utilizada")
    if invitacion.expires_at <= datetime.now(UTC):
        raise TokenExpiradoError("La invitación expiró")
    if invitacion.invitado_artista_id != actor_id:
        raise ForbiddenError("Esta invitación no es para ti")
    if await _pertenece_a_algun_sello(session, actor_id):
        raise ConflictError("Ya perteneces a un sello")

    # Reactiva la membresía si el artista ya estuvo en este sello; si no, inserta.
    membresia = await session.scalar(
        select(SelloArtista).where(
            SelloArtista.sello_id == invitacion.sello_id,
            SelloArtista.artista_id == actor_id,
        )
    )
    if membresia is None:
        session.add(
            SelloArtista(
                sello_id=invitacion.sello_id,
                artista_id=actor_id,
                rol=invitacion.rol,
                activo=True,
            )
        )
    else:
        membresia.rol = invitacion.rol
        membresia.activo = True

    invitacion.estado = EstadoInvitacionSello.aceptada
    invitacion.consumed_at = datetime.now(UTC)

    await bitacora_service.registrar(
        session,
        accion="Aceptación de invitación a sello",
        entidad="sello",
        entidad_id=str(invitacion.sello_id),
        autor_id=actor_id,
        detalle={"rol": invitacion.rol.value},
    )
    await session.commit()

    sello = await session.get(SelloDiscografico, invitacion.sello_id)
    return await _build_detalle(session, storage, sello, invitacion.rol.value)


async def get_invitacion(
    session: AsyncSession, storage: StorageService, token: str
) -> InvitacionDetalleDTO:
    """Lee el detalle de una invitación SIN consumirla (para la pantalla T14).

    → 400 si el token no existe. El estado se reporta como `expirada` si venció.
    """
    inv = await session.scalar(
        select(InvitacionSello).where(InvitacionSello.token == token)
    )
    if inv is None:
        raise TokenInvalidoError("Invitación inválida")

    sello = await session.get(SelloDiscografico, inv.sello_id)
    invitador = (
        await session.get(Usuario, inv.invitado_por) if inv.invitado_por else None
    )
    estado = inv.estado.value
    if estado == EstadoInvitacionSello.pendiente.value and inv.expires_at <= datetime.now(
        UTC
    ):
        estado = "expirada"

    return InvitacionDetalleDTO(
        sello_nombre=sello.nombre if sello else "—",
        sello_logo_url=await _logo_url(storage, sello) if sello else None,
        invitador=invitador.nombre_completo if invitador else None,
        rol=inv.rol.value,
        estado=estado,
        expires_at=inv.expires_at,
    )


async def rechazar_invitacion(
    session: AsyncSession, actor_id: uuid.UUID, token: str
) -> None:
    """El artista invitado rechaza la invitación (la marca rechazada)."""
    inv = (
        await session.execute(
            select(InvitacionSello)
            .where(InvitacionSello.token == token)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if inv is None:
        raise TokenInvalidoError("Invitación inválida")
    if (
        inv.estado != EstadoInvitacionSello.pendiente
        or inv.consumed_at is not None
    ):
        raise TokenConsumidoError("La invitación ya fue utilizada")
    if inv.expires_at <= datetime.now(UTC):
        raise TokenExpiradoError("La invitación expiró")
    if inv.invitado_artista_id != actor_id:
        raise ForbiddenError("Esta invitación no es para ti")

    inv.estado = EstadoInvitacionSello.rechazada
    inv.consumed_at = datetime.now(UTC)
    await bitacora_service.registrar(
        session,
        accion="Rechazo de invitación a sello",
        entidad="sello",
        entidad_id=str(inv.sello_id),
        autor_id=actor_id,
    )
    await session.commit()


async def eliminar_miembro(
    session: AsyncSession,
    actor_id: uuid.UUID,
    sello_id: uuid.UUID,
    artista_id: uuid.UUID,
) -> None:
    """Saca a un artista del sello (soft-delete). Solo owner.

    → 404 si el sello o el miembro no existen; 403 si el actor no es owner;
    409 si el owner intenta eliminarse a sí mismo (debe transferir primero).
    """
    sello = await session.get(SelloDiscografico, sello_id)
    if sello is None:
        raise NotFoundError("Sello no encontrado")

    await _require_rol(session, sello_id, actor_id, _SOLO_OWNER)

    if artista_id == actor_id:
        raise ConflictError(
            "No puedes eliminarte a ti mismo; transfiere el ownership primero"
        )

    objetivo = await _membership(session, sello_id, artista_id)
    if objetivo is None:
        raise NotFoundError("Ese artista no es miembro del sello")

    objetivo.activo = False
    await bitacora_service.registrar(
        session,
        accion="Eliminación de miembro de sello",
        entidad="sello",
        entidad_id=str(sello_id),
        autor_id=actor_id,
        detalle={"artista_id": str(artista_id)},
    )
    await session.commit()


async def transferir_ownership(
    session: AsyncSession,
    storage: StorageService,
    actor_id: uuid.UUID,
    sello_id: uuid.UUID,
    nuevo_owner_id: uuid.UUID,
) -> SelloDetalleDTO:
    """Transfiere el ownership a otro miembro activo del sello. Solo owner.

    El owner actual pasa a `manager` y el nuevo a `owner`. → 404 si el sello o el
    nuevo owner no son válidos; 403 si el actor no es owner; 422 si se transfiere
    a sí mismo.
    """
    sello = await session.get(SelloDiscografico, sello_id)
    if sello is None:
        raise NotFoundError("Sello no encontrado")

    actual = await _require_rol(session, sello_id, actor_id, _SOLO_OWNER)

    if nuevo_owner_id == actor_id:
        raise ValidationError("Ya eres el owner del sello")

    nuevo = await _membership(session, sello_id, nuevo_owner_id)
    if nuevo is None:
        raise NotFoundError("Ese artista no es miembro del sello")

    actual.rol = RolSelloArtista.manager
    nuevo.rol = RolSelloArtista.owner

    await bitacora_service.registrar(
        session,
        accion="Transferencia de ownership de sello",
        entidad="sello",
        entidad_id=str(sello_id),
        autor_id=actor_id,
        detalle={"nuevo_owner": str(nuevo_owner_id)},
    )
    await session.commit()

    return await _build_detalle(session, storage, sello, actual.rol.value)


async def salir_del_sello(
    session: AsyncSession,
    actor_id: uuid.UUID,
    sello_id: uuid.UUID,
) -> None:
    """El artista en sesión sale del sello (soft-delete).

    → 404 si el sello no existe o no es miembro; 409 si es el único owner
    (debe transferir el ownership antes de salir).
    """
    sello = await session.get(SelloDiscografico, sello_id)
    if sello is None:
        raise NotFoundError("Sello no encontrado")

    membresia = await _membership(session, sello_id, actor_id)
    if membresia is None:
        raise NotFoundError("No perteneces a este sello")

    if membresia.rol == RolSelloArtista.owner:
        owners = await session.scalar(
            select(func.count())
            .select_from(SelloArtista)
            .where(
                SelloArtista.sello_id == sello_id,
                SelloArtista.rol == RolSelloArtista.owner,
                SelloArtista.activo.is_(True),
            )
        )
        if owners <= 1:
            raise ConflictError(
                "Eres el único owner; transfiere el ownership antes de salir"
            )

    membresia.activo = False
    await bitacora_service.registrar(
        session,
        accion="Salida de sello",
        entidad="sello",
        entidad_id=str(sello_id),
        autor_id=actor_id,
        detalle={"rol": membresia.rol.value},
    )
    await session.commit()


async def listar_artistas(
    session: AsyncSession,
    storage: StorageService,
    actor_id: uuid.UUID,
    sello_id: uuid.UUID,
) -> list[MiembroDTO]:
    """Lista los artistas del sello (activos e inactivos) con rol y estado.

    Requiere que el actor sea miembro activo del sello. → 404 si el sello no
    existe; 403 si el actor no pertenece al sello.
    """
    sello = await session.get(SelloDiscografico, sello_id)
    if sello is None:
        raise NotFoundError("Sello no encontrado")

    if await _membership(session, sello_id, actor_id) is None:
        raise ForbiddenError("No perteneces a este sello")

    rows = (
        await session.execute(
            select(Usuario, SelloArtista.rol, SelloArtista.activo)
            .join(SelloArtista, SelloArtista.artista_id == Usuario.id)
            .where(SelloArtista.sello_id == sello_id)
        )
    ).all()

    miembros = [await _to_miembro(storage, u, rol, activo) for u, rol, activo in rows]
    # Activos primero, luego por jerarquía de rol.
    miembros.sort(key=lambda m: (not m.activo, _ROL_ORDEN.get(m.rol, 99)))
    return miembros
