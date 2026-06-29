"""DTOs Pydantic para el perfil del usuario (módulo users)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserMeDTO(BaseModel):
    """Datos del usuario en sesión. Nunca incluye `password_hash`."""

    id: str
    nombre_completo: str
    correo: EmailStr
    tipo: str
    activo: bool
    # Presigned URL de la foto (TTL), generada al servir. None si no hay foto.
    foto_url: str | None = None
    # Solo curadores: estado de su solicitud (pendiente/aprobada/rechazada) o None.
    estado_curador: str | None = None


class UserUpdateDTO(BaseModel):
    """Campos editables del perfil propio (T6). Los no listados se ignoran.

    `sello_discografico` se omite por decisión de producto (el sello es entidad
    propia, se modelará en una fase futura). Por ahora solo el nombre es editable.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_completo: str | None = Field(default=None, min_length=2, max_length=255)
