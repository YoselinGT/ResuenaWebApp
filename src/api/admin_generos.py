"""Router admin de géneros musicales (`/admin/generos`).

Solo accesible para usuarios con perfil Admin (1). Los services lanzan
excepciones de dominio; este router las traduce a códigos HTTP.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.middleware.auth import CurrentUser
from src.middleware.roles import require_admin
from src.models.dto.generos import (
    CategoriaCreateBody,
    CategoriaDTO,
    CategoriaUpdateBody,
    GeneroAdminDTO,
    GeneroCreateBody,
    GeneroUpdateBody,
)
from src.services import generos_service

router = APIRouter(prefix="/admin/generos", tags=["admin-generos"])


# ── GET /admin/generos ──────────────────────────────────────────


@router.get("", response_model=list[GeneroAdminDTO])
async def list_generos(
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> list[GeneroAdminDTO]:
    generos = await generos_service.list_generos_admin(session)
    return [
        GeneroAdminDTO(
            id=g.id,
            nombre=g.nombre,
            activo=g.activo,
            categorias=[
                CategoriaDTO(id=c.id, nombre=c.nombre, activo=c.activo)
                for c in g.categorias
            ],
        )
        for g in generos
    ]


# ── POST /admin/generos ─────────────────────────────────────────


@router.post("", response_model=GeneroAdminDTO, status_code=status.HTTP_201_CREATED)
async def create_genero(
    body: GeneroCreateBody,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> GeneroAdminDTO:
    genero = await generos_service.create_genero(session, body.nombre)
    await session.commit()
    return GeneroAdminDTO(
        id=genero.id,
        nombre=genero.nombre,
        activo=genero.activo,
        categorias=[],
    )


# ── PATCH /admin/generos/:id ────────────────────────────────────


@router.patch("/{genero_id}", response_model=GeneroAdminDTO)
async def update_genero(
    genero_id: int,
    body: GeneroUpdateBody,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> GeneroAdminDTO:
    genero = await generos_service.update_genero(
        session, genero_id, nombre=body.nombre, activo=body.activo
    )
    await session.commit()
    return GeneroAdminDTO(
        id=genero.id,
        nombre=genero.nombre,
        activo=genero.activo,
        categorias=[
            CategoriaDTO(id=c.id, nombre=c.nombre, activo=c.activo)
            for c in genero.categorias
        ],
    )


# ── DELETE /admin/generos/:id ───────────────────────────────────


@router.delete("/{genero_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_genero(
    genero_id: int,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
):
    await generos_service.delete_genero(session, genero_id)
    await session.commit()


# ── GET /admin/generos/:id/categorias ───────────────────────────


@router.get("/{genero_id}/categorias", response_model=list[CategoriaDTO])
async def list_categorias(
    genero_id: int,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> list[CategoriaDTO]:
    cats = await generos_service.list_categorias(session, genero_id)
    return [CategoriaDTO(id=c.id, nombre=c.nombre, activo=c.activo) for c in cats]


# ── POST /admin/generos/:id/categorias ──────────────────────────


@router.post(
    "/{genero_id}/categorias",
    response_model=CategoriaDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_categoria(
    genero_id: int,
    body: CategoriaCreateBody,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> CategoriaDTO:
    cat = await generos_service.create_categoria(session, genero_id, body.nombre)
    await session.commit()
    return CategoriaDTO(id=cat.id, nombre=cat.nombre, activo=cat.activo)


# ── PATCH /admin/categorias/:id ─────────────────────────────────


@router.patch("/categorias/{categoria_id}", response_model=CategoriaDTO)
async def update_categoria(
    categoria_id: int,
    body: CategoriaUpdateBody,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
) -> CategoriaDTO:
    cat = await generos_service.update_categoria(
        session, categoria_id, nombre=body.nombre, activo=body.activo
    )
    await session.commit()
    return CategoriaDTO(id=cat.id, nombre=cat.nombre, activo=cat.activo)


# ── DELETE /admin/categorias/:id ────────────────────────────────


@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_categoria(
    categoria_id: int,
    session: AsyncSession = Depends(get_session),
    _user: CurrentUser = Depends(require_admin),
):
    await generos_service.delete_categoria(session, categoria_id)
    await session.commit()
