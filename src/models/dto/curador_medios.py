"""DTOs Pydantic para la gestión de medios del curador (unificado).

Usado tanto en onboarding como en el dashboard post-onboarding.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import TipoMedio, TipoRedSocial


# ── Redes sociales del canal ────────────────────────────────────


class MedioRedDTO(BaseModel):
    """Red social de un canal del curador (input)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo: TipoRedSocial
    url: str = Field(min_length=3, max_length=500)
    es_principal: bool = False


class MedioRedOutDTO(BaseModel):
    """Red social de un canal del curador (output)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tipo: str
    url: str
    es_principal: bool


# ── Estadísticas ────────────────────────────────────────────────


class MedioStatsDTO(BaseModel):
    """Estadísticas agregadas de un medio."""

    recibidas: int = 0
    aceptadas: int = 0
    entregadas: int = 0
    tasa_aceptacion: float = 0.0


class MesStatDTO(BaseModel):
    mes: str  # YYYY-MM
    recibidas: int


class MedioStatsDetalleDTO(MedioStatsDTO):
    """Estadísticas detalladas de un medio (panel individual)."""

    por_mes: list[MesStatDTO] = []
    generos_frecuentes: list[int] = []
    tiempo_respuesta_horas: float | None = None


# ── Bodies (input) ──────────────────────────────────────────────


class MedioCreateBody(BaseModel):
    """Alta de un medio (onboarding o dashboard)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=255)
    tipo: TipoMedio
    descripcion: str | None = None
    audiencia_estimada: int | None = Field(default=None, ge=0)
    precio_creditos: int = Field(default=1, ge=1)
    descripcion_precio: str | None = Field(default=None, max_length=100)
    genero_ids: list[int] = Field(default_factory=list)
    categoria_ids: list[int] = Field(default_factory=list)
    redes: list[MedioRedDTO] = Field(
        min_length=1,
        description="Al menos una red social del canal",
    )


class MedioUpdateBody(BaseModel):
    """Edición parcial de un medio. Los campos None no se tocan."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    descripcion: str | None = None
    audiencia_estimada: int | None = Field(default=None, ge=0)
    precio_creditos: int | None = Field(default=None, ge=1)
    descripcion_precio: str | None = None
    genero_ids: list[int] | None = None
    categoria_ids: list[int] | None = None
    redes: list[MedioRedDTO] | None = None


# ── Responses (output) ──────────────────────────────────────────


class MedioOutDTO(BaseModel):
    """Medio del curador (unificado para onboarding y dashboard)."""

    id: str
    nombre: str
    tipo: str
    url: str | None = None
    descripcion: str | None = None
    audiencia_estimada: int | None = None
    precio_creditos: int = 1
    descripcion_precio: str | None = None
    estado_revision: str = "pendiente"
    motivo_rechazo: str | None = None
    activo: bool = True
    genero_ids: list[int] = []
    categoria_ids: list[int] = []
    redes: list[MedioRedOutDTO] = []
    stats: MedioStatsDTO | None = None


# ── Compatibilidad: aliases para imports existentes ─────────────

# Onboarding usa estos nombres
CuradorMedioDTO = MedioCreateBody
CuradorMedioOutDTO = MedioOutDTO
CuradorMedioRedDTO = MedioRedDTO
CuradorMedioRedOutDTO = MedioRedOutDTO

# Dashboard usa estos nombres
MedioConStatsDTO = MedioOutDTO
