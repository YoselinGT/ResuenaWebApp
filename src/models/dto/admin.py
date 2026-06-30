"""DTOs Pydantic del panel de administración."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SolicitudItemDTO(BaseModel):
    """Una solicitud de curador en el listado/detalle admin."""

    id: str
    usuario_id: str
    nombre_completo: str
    correo: str
    estado: str
    tipo_profesional: str | None = None
    url_portfolio: str | None = None
    notas_revision: str | None = None
    revisor_id: str | None = None
    created_at: datetime


class PaginatedSolicitudesDTO(BaseModel):
    items: list[SolicitudItemDTO]
    total: int
    page: int
    page_size: int


class RedDTO(BaseModel):
    tipo: str
    url: str


class SolicitudDetalleDTO(SolicitudItemDTO):
    """Detalle de una solicitud: incluye las redes sociales del curador."""

    redes: list[RedDTO] = []


class RechazarBody(BaseModel):
    """Motivo del rechazo de una solicitud (se envía al curador por email)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    motivo: str = Field(min_length=3, max_length=1000)


# ── Usuarios ─────────────────────────────────────────────────────
class UsuarioAdminDTO(BaseModel):
    """Un usuario en el listado/gestión admin (sin password_hash)."""

    id: str
    nombre_completo: str
    correo: str
    tipo: str
    perfil_id: int
    activo: bool
    created_at: datetime


class PaginatedUsuariosDTO(BaseModel):
    items: list[UsuarioAdminDTO]
    total: int
    page: int
    page_size: int


class UsuarioAdminUpdate(BaseModel):
    """Campos editables por admin. Correo/contraseña/tipo NO editables."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_completo: str | None = Field(default=None, min_length=2, max_length=255)
    activo: bool | None = None
