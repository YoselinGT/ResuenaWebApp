"""Servicio de perfil de usuario.

Lógica de lectura/actualización del usuario en sesión. Las URLs de foto se
generan como presigned (TTL) vía `StorageService` al momento de servir; la BD
solo guarda la clave en `foto_path`.
"""

from __future__ import annotations

import uuid
from io import BytesIO

import magic
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.storage import StorageService
from src.models.dto.users import UserMeDTO, UserUpdateDTO
from src.models.enums import TipoUsuario
from src.models.solicitudes_curador import SolicitudCurador
from src.models.usuarios import Usuario
from src.services import bitacora_service
from src.services.exceptions import (
    UnauthorizedError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from src.utils.sanitize import clean_text

# TTL de las URLs presigned de foto de perfil (1 hora).
FOTO_URL_TTL_SECONDS = 3600

# Foto de perfil: solo JPEG, cuadrada 200×200.
FOTO_MIME_PERMITIDO = "image/jpeg"
FOTO_SIZE_PX = 200
FOTO_MAX_BYTES = 5 * 1024 * 1024  # 5 MB de entrada
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


def _procesar_avatar(data: bytes) -> bytes:
    """Valida el MIME real y devuelve un JPEG cuadrado 200×200.

    El MIME se valida por contenido (libmagic), nunca por la extensión ni el
    Content-Type del cliente. Reabrir y reencodear con Pillow además normaliza
    la imagen y descarta metadatos/payloads embebidos.
    """
    if len(data) > FOTO_MAX_BYTES:
        raise ValidationError("La imagen supera el tamaño máximo (5 MB)")

    mime = magic.from_buffer(data, mime=True)
    if mime != FOTO_MIME_PERMITIDO:
        raise UnsupportedMediaTypeError("Solo se admiten imágenes JPEG")

    try:
        with Image.open(BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            cuadrada = ImageOps.fit(
                img.convert("RGB"),
                (FOTO_SIZE_PX, FOTO_SIZE_PX),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            out = BytesIO()
            cuadrada.save(out, format="JPEG", quality=85, optimize=True)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("La imagen no se pudo procesar") from exc

    return out.getvalue()


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

    jpeg = _procesar_avatar(data)
    key = f"{FOTO_PREFIX}/{usuario_id}.jpg"
    await storage.upload(key, jpeg, FOTO_MIME_PERMITIDO)

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
