"""DTOs Pydantic para onboarding, perfil y catálogos."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import TipoLanzamientos, TipoMedio, TipoRedSocial


# ── Catálogos (salida) ───────────────────────────────────────────
class GeneroDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class IdiomaDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str


class RegionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo: str
    nombre: str


# ── Bodies de guardado por paso ──────────────────────────────────
class GenerosBody(BaseModel):
    genero_ids: list[int] = Field(min_length=1)


class IdiomasBody(BaseModel):
    codigos: list[str] = Field(min_length=1)


class RegionesBody(BaseModel):
    codigos: list[str] = Field(min_length=1)


class PreferenciasBody(BaseModel):
    apertura_musical: int = Field(ge=0, le=100, default=50)
    acepta_todos_idiomas: bool = False
    tipo_lanzamientos: TipoLanzamientos | None = None


# ── Redes sociales ───────────────────────────────────────────────
class RedSocialDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    tipo: TipoRedSocial
    url: str = Field(min_length=3, max_length=500)


class RedSocialOutDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tipo: str
    url: str


# ── Medios del curador ───────────────────────────────────────────
class CuradorMedioRedDTO(BaseModel):
    """Red social de un canal del curador (input)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo: TipoRedSocial
    url: str = Field(min_length=3, max_length=500)
    es_principal: bool = False


class CuradorMedioRedOutDTO(BaseModel):
    """Red social de un canal del curador (output)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tipo: str
    url: str
    es_principal: bool


class CuradorMedioDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre: str = Field(min_length=1, max_length=255)
    tipo: TipoMedio
    descripcion: str | None = None
    audiencia_estimada: int | None = Field(default=None, ge=0)
    precio_creditos: int = Field(default=1, ge=1)
    descripcion_precio: str | None = Field(default=None, max_length=100)
    genero_ids: list[int] = Field(default_factory=list)
    redes: list[CuradorMedioRedDTO] = Field(
        min_length=1,
        description="Al menos una red social del canal",
    )


class CuradorMedioOutDTO(BaseModel):
    id: str
    nombre: str
    tipo: str
    url: str | None
    descripcion: str | None
    audiencia_estimada: int | None
    precio_creditos: int
    descripcion_precio: str | None
    genero_ids: list[int]
    redes: list[CuradorMedioRedOutDTO] = []


# ── Progreso del onboarding ──────────────────────────────────────
class OnboardingProgressDTO(BaseModel):
    generos: bool = False
    idiomas: bool = False
    regiones: bool = False
    redes: bool = False
    medios: bool = False
    preferencias: bool = False
    medios_count: int = 0
