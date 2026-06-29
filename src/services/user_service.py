"""Servicio de perfil de usuario.

Lógica de lectura/actualización del usuario en sesión. Las URLs de foto se
generan como presigned (TTL) vía `StorageService` al momento de servir; la BD
solo guarda la clave en `foto_path`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.storage import StorageService
from src.models.dto.users import UserMeDTO, UserUpdateDTO
from src.models.enums import TipoUsuario
from src.models.solicitudes_curador import SolicitudCurador
from src.models.usuarios import Usuario
from src.services import bitacora_service
from src.services.exceptions import UnauthorizedError, ValidationError
from src.utils.images import JPEG_MIME, process_jpeg_square
from src.utils.sanitize import clean_text

# TTL de las URLs presigned de foto de perfil (1 hora).
FOTO_URL_TTL_SECONDS = 3600

# Foto de perfil: cuadrada 200×200.
FOTO_SIZE_PX = 200
FOTO_PREFIX = "perfiles-avatar"


async def _estado_solicitud_curador(
    session: AsyncSession, usuario_id: uuid.UUID
) -> str | None:
    """Estado de la solicitud de curador más reciente, o None si no hay."""
    estado = await session.scalar(
        select(SolicitudCurador.estado)
        .where(SolicitudCurador.usuario_id == usuario_id)
        .order_by(SolicitudCurador.created_at.desc())
        .limit(1)
    )
    return estado.value if estado is not None else None


async def get_me(
    session: AsyncSession,
    storage: StorageService,
    usuario_id: uuid.UUID,
) -> UserMeDTO:
    """Devuelve el perfil del usuario en sesión (sin password_hash)."""
    usuario = await session.get(Usuario, usuario_id)
    if usuario is None:
        raise UnauthorizedError("Usuario no encontrado")

    foto_url = (
        await storage.presigned_url(usuario.foto_path, FOTO_URL_TTL_SECONDS)
        if usuario.foto_path
        else None
    )

    estado_curador = None
    if usuario.tipo == TipoUsuario.curador:
        estado_curador = await _estado_solicitud_curador(session, usuario_id)

    return UserMeDTO(
        id=str(usuario.id),
        nombre_completo=usuario.nombre_completo,
        correo=usuario.correo,
        tipo=usuario.tipo.value,
        activo=usuario.activo,
        foto_url=foto_url,
        estado_curador=estado_curador,
    )


async def update_me(
    session: AsyncSession,
    storage: StorageService,
    usuario_id: uuid.UUID,
    dto: UserUpdateDTO,
) -> UserMeDTO:
    """Actualiza campos editables del perfil propio.

    Solo `nombre_completo` es editable; cualquier otro campo enviado se ignora
    (no está en el DTO). Sanitiza la entrada, registra un diff en bitácora y
    no toca nada si no hay cambios efectivos.
    """
    usuario = await session.get(Usuario, usuario_id)
    if usuario is None:
        raise UnauthorizedError("Usuario no encontrado")

    cambios: dict[str, dict[str, str | None]] = {}

    if dto.nombre_completo is not None:
        nuevo = clean_text(dto.nombre_completo)
        if not nuevo or len(nuevo) < 2:
            raise ValidationError("El nombre no es válido")
        if nuevo != usuario.nombre_completo:
            cambios["nombre_completo"] = {
                "antes": usuario.nombre_completo,
                "despues": nuevo,
            }
            usuario.nombre_completo = nuevo

    if cambios:
        await bitacora_service.registrar(
            session,
            accion="Actualización de perfil propio",
            entidad="usuario",
            entidad_id=str(usuario_id),
            autor_id=usuario_id,
            detalle={"cambios": cambios},
        )
        await session.commit()

    return await get_me(session, storage, usuario_id)


async def set_photo(
    session: AsyncSession,
    storage: StorageService,
    usuario_id: uuid.UUID,
    data: bytes,
) -> UserMeDTO:
    """Procesa y guarda la foto de perfil. Devuelve el perfil actualizado.

    En BD se guarda la **clave** S3 (`perfiles-avatar/<id>.jpg`), nunca la URL.
    """
    usuario = await session.get(Usuario, usuario_id)
    if usuario is None:
        raise UnauthorizedError("Usuario no encontrado")

    jpeg = process_jpeg_square(data, size=FOTO_SIZE_PX)
    key = f"{FOTO_PREFIX}/{usuario_id}.jpg"
    await storage.upload(key, jpeg, JPEG_MIME)

    usuario.foto_path = key
    await session.commit()

    return await get_me(session, storage, usuario_id)


async def delete_photo(
    session: AsyncSession,
    storage: StorageService,
    usuario_id: uuid.UUID,
) -> UserMeDTO:
    """Elimina la foto de perfil (objeto S3 + `foto_path`). Idempotente."""
    usuario = await session.get(Usuario, usuario_id)
    if usuario is None:
        raise UnauthorizedError("Usuario no encontrado")

    if usuario.foto_path:
        await storage.delete(usuario.foto_path)
        usuario.foto_path = None
        await session.commit()

    return await get_me(session, storage, usuario_id)
