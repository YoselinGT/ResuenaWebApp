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


class CanalRedDTO(BaseModel):
    """Red social de un canal en contexto de revisión admin."""

    tipo: str
    url: str
    es_principal: bool = False


class CanalRevisionDTO(BaseModel):
    """Canal de un curador en contexto de revisión admin."""

    id: str
    nombre: str
    tipo: str
    url: str | None = None
    descripcion: str | None = None
    audiencia_estimada: int | None = None
    precio_creditos: int = 1
    descripcion_precio: str | None = None
    generos: list[str] = []
    categorias: list[str] = []
    redes: list[CanalRedDTO] = []
    estado_revision: str = "pendiente"
    motivo_rechazo: str | None = None
    revisado_at: datetime | None = None


class CanalAdminDTO(BaseModel):
    """Canal en el listado admin — incluye info del curador."""

    id: str
    nombre: str
    tipo: str
    descripcion: str | None = None
    audiencia_estimada: int | None = None
    precio_creditos: int = 1
    descripcion_precio: str | None = None
    estado_revision: str = "pendiente"
    motivo_rechazo: str | None = None
    revisado_at: datetime | None = None
    curador_id: str
    curador_nombre: str
    curador_correo: str
    generos: list[str] = []
    categorias: list[str] = []
    redes: list[CanalRedDTO] = []
    created_at: datetime


class PaginatedCanalesDTO(BaseModel):
    items: list[CanalAdminDTO]
    total: int
    page: int
    page_size: int


class CanalDetalleAdminDTO(CanalAdminDTO):
    """Detalle de un canal — incluye redes sociales, géneros y categorías completos."""

    redes: list[CanalRedDTO] = []
    generos: list[str] = []
    categorias: list[str] = []


class SolicitudDetalleDTO(SolicitudItemDTO):
    """Detalle de una solicitud: incluye los canales del curador."""

    redes: list[RedDTO] = []
    canales: list[CanalRevisionDTO] = []


class RechazarBody(BaseModel):
    """Motivo del rechazo de una solicitud (se envía al curador por email)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    motivo: str = Field(min_length=3, max_length=1000)


class RechazarCanalBody(BaseModel):
    """Motivo del rechazo de un canal individual."""

    model_config = ConfigDict(str_strip_whitespace=True)

    motivo: str = Field(min_length=10, max_length=1000)


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
