"""Procesamiento de imágenes para subidas (avatares, logos).

Valida el MIME real con libmagic (nunca por extensión ni Content-Type del
cliente) y reencodea con Pillow, lo que además descarta metadatos/payloads
embebidos. Solo se admite JPEG.
"""

from __future__ import annotations

from io import BytesIO

import magic
from PIL import Image, ImageOps, UnidentifiedImageError

from src.services.exceptions import UnsupportedMediaTypeError, ValidationError

JPEG_MIME = "image/jpeg"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def process_jpeg_square(
    data: bytes,
    *,
    size: int,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> bytes:
    """Devuelve un JPEG cuadrado `size`×`size` (center-crop).

    Lanza `UnsupportedMediaTypeError` (→415) si el contenido no es JPEG y
    `ValidationError` (→422) si excede el tamaño o no se puede decodificar.
    """
    if len(data) > max_bytes:
        raise ValidationError(
            f"La imagen supera el tamaño máximo ({max_bytes // (1024 * 1024)} MB)"
        )

    if magic.from_buffer(data, mime=True) != JPEG_MIME:
        raise UnsupportedMediaTypeError("Solo se admiten imágenes JPEG")

    try:
        with Image.open(BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            cuadrada = ImageOps.fit(
                img.convert("RGB"),
                (size, size),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            out = BytesIO()
            cuadrada.save(out, format="JPEG", quality=85, optimize=True)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError("La imagen no se pudo procesar") from exc

    return out.getvalue()
