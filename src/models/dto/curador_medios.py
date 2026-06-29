"""DTOs Pydantic para la gestión de medios del curador (post-onboarding)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import TipoMedio


class MedioStatsDTO(BaseModel):
    """Estadísticas agregadas de un medio."""

    recibidas: int = 0
    aceptadas: int = 0
    entregadas: int = 0
    tasa_aceptacion: float = 0.0


class MedioConStatsDTO(BaseModel):
    """Medio del curador con sus estadísticas compactas."""

    id: str
    nombre: str
    tipo: str
    url: str | None = None
    descripcion: str | None = None
    audiencia_estimada: int | None = None
    activo: bool
    genero_ids: list[int] = []
    stats: MedioStatsDTO


class MedioCreateBody(BaseModel):
    """Alta de un medio post-onboarding."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=255)
    tipo: TipoMedio
    url: str | None = Field(default=None, max_length=500)
    descripcion: str | None = None
    audiencia_estimada: int | None = Field(default=None, ge=0)
    generos_especializados: list[int] = Field(default_factory=list)


class MedioUpdateBody(BaseModel):
    """Edición parcial de un medio. Los campos None no se tocan."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    url: str | None = Field(default=None, max_length=500)
    descripcion: str | None = None
    audiencia_estimada: int | None = Field(default=None, ge=0)
    generos_especializados: list[int] | None = None


class MesStatDTO(BaseModel):
    mes: str  # YYYY-MM
    recibidas: int


class MedioStatsDetalleDTO(MedioStatsDTO):
    """Estadísticas detalladas de un medio (panel individual)."""

    por_mes: list[MesStatDTO] = []
    # Pendiente de Fase 08 (esquema de campañas con género y timestamps de
    # respuesta): por ahora vacío / None.
    generos_frecuentes: list[int] = []
    tiempo_respuesta_horas: float | None = None
