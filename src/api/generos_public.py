"""Router público de géneros musicales (`/generos`).

Endpoint público para que artistas y curadores vean los géneros activos
con sus categorías activas anidadas. No requiere autenticación.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.models.dto.generos import CategoriaDTO, GeneroPublicDTO
from src.services import generos_service

router = APIRouter(prefix="/generos", tags=["generos"])


@router.get("", response_model=list[GeneroPublicDTO])
async def list_generos(
    session: AsyncSession = Depends(get_session),
) -> list[GeneroPublicDTO]:
    """Géneros activos con categorías activas anidadas."""
    generos = await generos_service.list_generos_public(session)
    return [
        GeneroPublicDTO(
            id=g.id,
            nombre=g.nombre,
            categorias=[
                CategoriaDTO(id=c.id, nombre=c.nombre, activo=c.activo)
                for c in g.categorias
            ],
        )
        for g in generos
    ]
