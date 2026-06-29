"""DTOs Pydantic del módulo de sellos discográficos."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


class SelloOutDTO(BaseModel):
    """Datos públicos de un sello (con la URL de logo presigned si existe)."""

    id: str
    nombre: str
    descripcion: str | None = None
    website: str | None = None
    logo_url: str | None = None
    # Rol del usuario en sesión dentro de este sello (owner/manager/artista).
    rol: str | None = None


class MiembroDTO(BaseModel):
    """Un artista miembro de un sello, con su rol."""

    id: str
    nombre_completo: str
    correo: str
    rol: str
    activo: bool
    foto_url: str | None = None


class SelloDetalleDTO(SelloOutDTO):
    """Sello + lista de miembros (para el panel de gestión)."""

    miembros: list[MiembroDTO] = []


class InvitarBody(BaseModel):
    """Body de invitación a un sello. El rol no puede ser `owner`."""

    model_config = ConfigDict(str_strip_whitespace=True)

    correo: EmailStr
    rol: Literal["manager", "artista"]


class InvitacionOutDTO(BaseModel):
    """Resumen de una invitación emitida."""

    id: str
    correo: str
    rol: str
    estado: str
    expires_at: datetime


class TransferOwnershipBody(BaseModel):
    """Body para transferir el ownership del sello a otro miembro."""

    nuevo_owner_id: uuid.UUID


class InvitacionDetalleDTO(BaseModel):
    """Detalle de una invitación para mostrar antes de aceptar/rechazar."""

    sello_nombre: str
    sello_logo_url: str | None = None
    invitador: str | None = None
    rol: str
    estado: str  # pendiente | aceptada | rechazada | expirada
    expires_at: datetime
