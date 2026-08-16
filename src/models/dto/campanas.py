"""DTOs Pydantic para campañas musicales."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ── Bodies (input) ──────────────────────────────────────────────


class CampanaCreateBody(BaseModel):
    """Body para crear una campaña (borrador)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=5000)
    genero_id: int


class CampanaUpdateBody(BaseModel):
    """Body para actualizar una campaña en borrador."""

    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=5000)
    genero_id: int | None = None


class CuradorSelectBody(BaseModel):
    """Body para vincular curadores a una campaña."""

    profesional_ids: list[str] = Field(min_length=1)


# ── Responses (output) ──────────────────────────────────────────


class CampanaMedioResponse(BaseModel):
    """Medio vinculado a una campaña."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    medio_id: str
    curador_id: str
    estado: str
    precio_snapshot: int
    creditos_retenidos: int
    fecha_limite: datetime | None = None


class CampanaResponse(BaseModel):
    """Respuesta de campaña."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    artista_id: str
    sello_id: str | None = None
    titulo: str
    descripcion: str | None = None
    url_audio: str | None = None
    url_imagen: str | None = None
    url_material: str | None = None
    genero_id: int
    estado: str
    creditos_usados: int
    created_at: datetime
    updated_at: datetime
    medios: list[CampanaMedioResponse] = []


class CampanaListResponse(BaseModel):
    """Item de campaña en listado."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    titulo: str
    estado: str
    genero_id: int
    creditos_usados: int
    url_imagen: str | None = None
    created_at: datetime
    updated_at: datetime


class CampanaEnvioResponse(BaseModel):
    """Respuesta al intentar enviar una campaña."""

    status: str  # "enviada" | "sin_creditos"
    creditos_necesarios: int | None = None
    creditos_disponibles: int | None = None
    creditos_faltantes: int | None = None
    campana: CampanaResponse | None = None


class CuradorDisponibleResponse(BaseModel):
    """Curador disponible para seleccionar."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre_completo: str
    tipo_profesional: str | None = None
    canales: list[CanalInfo] = []


class CanalInfo(BaseModel):
    """Canal de un curador."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    tipo: str
    audiencia_estimada: int | None = None
    precio_creditos: int = 1
    descripcion_precio: str | None = None
    categorias: list[str] = []


# Rebuild para referencias circulares
CuradorDisponibleResponse.model_rebuild()
