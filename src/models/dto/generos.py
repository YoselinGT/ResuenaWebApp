"""DTOs Pydantic para géneros musicales y categorías profesionales."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Categorías ──────────────────────────────────────────────────


class CategoriaDTO(BaseModel):
    """Categoría dentro de un género."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    activo: bool


class CategoriaCreateBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=100)


class CategoriaUpdateBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    activo: bool | None = None


# ── Géneros ─────────────────────────────────────────────────────


class GeneroAdminDTO(BaseModel):
    """Género con sus categorías anidadas (admin)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    activo: bool
    categorias: list[CategoriaDTO] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GeneroPublicDTO(BaseModel):
    """Género activo con categorías activas (público)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    categorias: list[CategoriaDTO] = []


class GeneroCreateBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=100)


class GeneroUpdateBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    activo: bool | None = None
