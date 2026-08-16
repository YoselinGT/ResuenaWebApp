"""Servicio de upload de archivos para campañas.

Maneja la validación de MIME types, límites de tamaño y subida a S3
vía StorageService. Los endpoints de upload nunca usan boto3 directamente.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from PIL import Image

from src.infra.storage import get_storage_service
from src.services.exceptions import ValidationError

# Límites de tamaño
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGEN_SIZE = 5 * 1024 * 1024  # 5MB
MAX_MATERIAL_SIZE = 100 * 1024 * 1024  # 100MB

# MIME types permitidos
AUDIO_MIMES = {"audio/mpeg", "audio/wav", "audio/mp3"}
IMAGEN_MIMES = {"image/jpeg", "image/png"}
MATERIAL_MIMES = {"application/zip", "application/x-zip-compressed"}

# Extensiones permitidas
AUDIO_EXT = {".mp3", ".wav"}
IMAGEN_EXT = {".jpg", ".jpeg", ".png"}
MATERIAL_EXT = {".zip"}


async def _validate_file(
    file: UploadFile,
    allowed_mimes: set[str],
    allowed_exts: set[str],
    max_size: int,
    tipo: str,
) -> bytes:
    """Valida y lee el contenido de un archivo upload."""
    # Validar extensión
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_exts:
        raise ValidationError(
            f"Extensión de archivo no permitida para {tipo}. "
            f"Permitidas: {', '.join(allowed_exts)}"
        )

    # Leer contenido
    content = await file.read()
    size = len(content)

    # Validar tamaño
    if size > max_size:
        max_mb = max_size // (1024 * 1024)
        raise ValidationError(
            f"El archivo excede el tamaño máximo de {max_mb}MB para {tipo}"
        )

    if size == 0:
        raise ValidationError("El archivo está vacío")

    return content


def _get_content_type(file: UploadFile, tipo: str) -> str:
    """Determina el content type del archivo."""
    ext = Path(file.filename or "").suffix.lower()

    if tipo == "audio":
        return "audio/mpeg" if ext == ".mp3" else "audio/wav"
    elif tipo == "imagen":
        return "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    elif tipo == "material":
        return "application/zip"

    return file.content_type or "application/octet-stream"


async def upload_audio(
    campana_id: uuid.UUID,
    file: UploadFile,
) -> str:
    """Sube audio de campaña a S3. Retorna la clave S3."""
    content = await _validate_file(
        file, AUDIO_MIMES, AUDIO_EXT, MAX_AUDIO_SIZE, "audio"
    )

    ext = Path(file.filename or "").suffix.lower()
    key = f"campanas-audio/{campana_id}/audio{ext}"
    content_type = _get_content_type(file, "audio")

    storage = get_storage_service()
    await storage.upload(key, content, content_type)
    return key


async def upload_imagen(
    campana_id: uuid.UUID,
    file: UploadFile,
) -> str:
    """Sube imagen de portada a S3. Redimensiona a 800x800 max. Retorna la clave S3."""
    import io

    content = await _validate_file(
        file, IMAGEN_MIMES, IMAGEN_EXT, MAX_IMAGEN_SIZE, "imagen"
    )

    # Redimensionar con Pillow
    try:
        img = Image.open(io.BytesIO(content))
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)

        # Convertir a JPEG si es PNG (para consistencia)
        output = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output, format="JPEG", quality=85)
        content = output.getvalue()
    except Exception:
        raise ValidationError("No se pudo procesar la imagen")

    key = f"campanas-imagenes/{campana_id}/cover.jpg"
    storage = get_storage_service()
    await storage.upload(key, content, "image/jpeg")
    return key


async def upload_material(
    campana_id: uuid.UUID,
    file: UploadFile,
) -> str:
    """Sube material adicional (ZIP) a S3. Retorna la clave S3."""
    content = await _validate_file(
        file, MATERIAL_MIMES, MATERIAL_EXT, MAX_MATERIAL_SIZE, "material"
    )

    key = f"campanas-material/{campana_id}/material.zip"
    storage = get_storage_service()
    await storage.upload(key, content, "application/zip")
    return key
